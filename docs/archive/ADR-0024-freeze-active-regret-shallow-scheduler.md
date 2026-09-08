# ADR-0024: Freeze the active-regret shallow scheduler

**Status:** Accepted; frozen before reserved evaluation

**Date:** 2026-08-19

## Decision

Freeze `river-post-probe-scheduler-v1` for the sequential river reserved gate.
The rule runs DCFR through checkpoint two, ranks the pool by raw accumulated
positive regret, and moves at most the top 12.5% to checkpoint six. Low-ranked
nonrecipients fall back to checkpoint two to fund those promotions. The
allocator cannot exceed fixed checkpoint four in either iterations or
deterministic alternating state visits. All other contexts stop at checkpoint
four.

Do not deploy the CFR+ shadow accumulator. It is a valid traversal-free
statistic, but it did not add enough independent information or strategy gain
to repay its conservative measured cost. The frozen rule pays only for one
active-regret summary and rank/macro allocation. Fixed checkpoint-four DCFR is
the permanent fallback.

## Development result

The 1,024-context shadow probe exactly reproduced every context provenance
digest and checkpoint-two active DCFR feature. Adding the shadow changed no
active regret or average-strategy accumulator and launched no additional tree
traversal. Shadowed solver time was 1.0017 times plain solver time, but
conservative per-context charging plus feature extraction cost 7.905% of the
plain two-iteration probe.

The shadow contains signal: raw shadow regret ranks raw future reduction per
state visit at Spearman `0.670`, compared with `0.618` for raw active regret.
However, their raw ranks correlate at `0.978`. The best shadow-bearing
development candidate improves final aggregate exploitability less than the
active-only winner and loses measured reduction per millisecond after charging
the probe overhead.

Five-fold board-group cross-validation selected `active_raw::shallow_12_5` in
four folds and `active_raw::shallow_25` in one. Every held-out fold improved
fixed checkpoint four. Aggregate raw exploitability uplift is `132.208`, which
captures 44.335% of the exact post-probe perfect-information uplift. Charged
raw reduction per millisecond improves by 2.330%. Candidate state work is below
fixed in every fold.

Fitting once on all development contexts selects
`active_raw::shallow_12_5`. It assigns 128 contexts to checkpoint two, 768 to
checkpoint four, and 128 to checkpoint six. Aggregate final exploitability
falls from `938.983` to `790.014`, a raw improvement of `148.969`, while using
926,336 versus 926,848 deterministic state visits. After 9.063 ms of feature
work and 1.343 ms of allocation work, measured reduction per millisecond is
2.509% above fixed checkpoint four.

## Limits and reserved protocol

This is a development pass, not held-out evidence. The score family was chosen
after inspecting active features on the development trace; internal folds test
the finite selection procedure but cannot erase that design dependence.

Commit the selected rule before constructing any reserved context. Generate
validation only, with the same seed, 400 group universe, four range families,
sequential tree, and DCFR checkpoints. The fixed rule must improve raw final
exploitability in every one of five validation group folds, capture at least
25% of the validation perfect post-probe uplift, remain within both work
budgets, and improve charged measured reduction per millisecond. If any gate
fails, retain fixed checkpoint four and do not retune or inspect test. If all
validation gates pass, evaluate the unchanged rule once on test under the same
gates.

## Dissent protocol

**Confidence:** high in causal construction and development arithmetic;
moderate in the small development effect; low in transfer beyond this river
tree.

**Opposing evidence:** the all-development final-quality gain is meaningful,
but the rate gain is only 2.51%; the allocator pools synthetic contexts as a
proxy for speculative jobs; and no multiplayer or earlier-street claim follows.

**Largest unknown:** whether raw regret retains the joint relationship among
utility scale, convergence state, and future work on unseen boards.

**Cheapest falsification:** the frozen validation split. No further development
feature or macro experiment is authorized before that result.
