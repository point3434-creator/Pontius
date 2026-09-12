# Combined-feature intervention on the observed evaluation panel

User authority: "Let's run the next test", following the proposed comparison of
original range/equity features plus saved witness predictions against predicted-only
grouping at matched capacity. This covers the diagnostic invocation, not publication.

Use all 48 evaluation cases in witness-distillation-001, already observed. Frozen
per-hand raw features and predictions are in witness-fit-diagnostic-001. No new boards,
model fits, parameter sweep, retained-control re-solves or deployment changes.

Two new methods are necessary to interpret the intervention: raw11 uses the eleven
original range/equity features alone; hybrid uses those eleven plus four saved witness
predictions. The retained range_response control uses nine response features, so it
cannot substitute for the raw11 ablation. Both methods use anchored_clusters unchanged
and each seat's occupied uniform-equity group count. Own-hand weights are unchanged.

Fix one scaling rule before evaluation. For each seat and feature block, compute
squared scale = mean over the 48 TRAINING cases of sum_h mu_h ||f_h - mean_mu(f)||^2.
Divide the raw block by its scalar RMS scale and the prediction block by its scalar
RMS scale. Require both scales positive and finite. Do not standardize individual
columns or center evaluation cases. Hybrid concatenates the two scaled blocks with
equal block weight. This equalizes training within-case squared-distance energy;
it is a fixed diagnostic choice, not a claim of optimal scaling. Raw11 uses the same
scaled raw block. No evaluation outcome enters scaling or method selection.

Primary: hybrid floor minus retained predicted-only floor. Essential ablation:
hybrid minus raw11 floor. Report range-equity, range-response, uniform-equity, direct
witness and full-hand comparisons too. Lower is better. Reuse all six sealed prior
floors, compute two new certified floors per case: 192 new LP calls total. Each LP
keeps the existing five-second and 10,000-iteration bounds. No candidate is selected
or adopted automatically. A win only over predicted-only is insufficient to claim
that learned predictions add value over the original features.

Rebuild each game and require saved inputs and raw features to match; require saved
predictions to reproduce from the unchanged model. Only original features and saved
predictions enter either new group construction. Targets and old solutions are used
after groups exist, only for comparison. Retain every case, groups, certificates,
all method floors and signed interval comparisons. Means give equal weight to eight
boards, each averaging three pools and two regimes. Report board/pool/regime/texture
breakdowns and leave-one-board-out means. No hand-independence, BB/100, new-board
generalization or population-confidence claim follows from this observed panel.

One Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0 worker, one BLAS thread, 600-second
worker limit, no RSS cap. Count LP entry calls and require exactly 192. Prohibit model
fitting. Parent reconstructs scales, inputs, features, groups and all new certificates
without additional LP calls before writing the summary. Preserve failures, no retry.
Retain worker and whole inner-command time, with the measurement boundary explicitly
ending before the final outer receipt write. Parent work is outside the worker bound.

Before scoring: synthetic weighted-scale, concatenation, invalid-scale and occupied
capacity checks. After completion: independent scalar scale and exact-rational
certificate/difference/aggregate audit, plus byte preservation of all input pins.
Standalone research artifacts only; no shared production source changes. Preserve
all earlier milestones and record this result, including any failure or nonimprovement.
