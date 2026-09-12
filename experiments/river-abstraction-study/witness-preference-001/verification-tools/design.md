# Small action-preference learning test

Authority: "Let's design and run a small test if you can please" approving the
preceding action-preference proposal. One observed-panel development invocation;
no commit, push, production change or adoption. Preserve all eleven prior milestones.

Three new representations: ordinary preference classification, decision-cost-weighted
preference classification, and exact teacher preferences (privileged reference).
Use original 48 training cases and all 48 already observed evaluation cases, eight
boards x three hand pools x two range regimes. No case selection, new boards or tuning.
Same eleven raw inputs, 78-column quadratic basis, four outputs, independent seat
models, float64, unpenalized intercept, lambda=.001 and occupied grouping capacities.
Learned outputs are sigmoid probabilities; exact outputs are 1 for positive witness
advantage, 0 for negative and .5 for an exact tie. Same anchored clustering consumes
the four features. No output clipping transform, feature scaling or new predictor input.

Each output uses binary cross entropy plus lambda/2 times squared slope coefficients.
Base training mass is each hand's normalized own marginal divided by 48 cases.
Ordinary classification uses that mass unchanged. Weighted classification multiplies
it by the ABSOLUTE FULL, UNCLIPPED witness advantage and normalizes the resulting
mass to sum to one per output over TRAINING ONLY. This deliberately shifts effective
case weights toward costly errors; base case sampling is unchanged. Record every
normalizer. It holds objective mass and regularization scale comparable, but does not
isolate every effect of weighting. Ties have .5 targets and zero cost weight. An
all-zero-cost output predicts .5; a constant positive-weight label predicts that label.

Deterministic damped Newton fits start at zero, stop at max gradient <=1e-8, max 80
iterations and 40 backtracks, Armijo .0001. No search/retry on nonconvergence. Save
four seat models (two methods x two seats, four outputs each) before evaluation.
Parent independently reconstructs training and repeats the four fits, matching the
models exactly. A separate scalar audit checks labels, normalizers, probabilities,
weighted gradients and strategic interval arithmetic without fitting or LP calls.

Primary contrast: weighted preference minus ordinary preference grouping floor.
Key references: range_response, exact preference representation and clipped exact
witness representation. Reuse all seven crossover floors without control re-solving.
Three methods x 48 cases x two asymmetric seat solves = exactly 288 new LP calls.
Record both-seat floors and each seat's signed contribution versus range_response;
also decompose weighted-minus-ordinary by seat. Existing five-second/10,000-iteration
per-LP limits remain. Parent optimization is disabled during certificate verification.

Report equal-board means, all board/pool/regime/texture/leave-one-board-out summaries,
signed numerical intervals and counts, and both preidentified board7 polarized cases.
Prediction diagnostics report expected wrong-action cost of each probability feature
against the fixed witnesses, not the resulting grouped strategy. They are secondary.
The witness bank is finite; exact action-preference features need not preserve an
optimal grouping. Repeated exact vectors are allocated by the fixed tie handling to
maintain capacity. Oracle supervision is never an input to either learned grouping.

This is an observed-data intervention, not reserved-board confirmation or measured
playing strength. The encoded game is two-player, one-bet river, not six-max play.
No change to natural-range assumptions or the synthetic polarization generator.

Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, one BLAS thread. Worker limit 600 seconds,
parent verification outside it, no RSS cap. Exclusive output, checked child exit and
captures, immutable input/source pins before and after, no automatic invocation retry.
Retain models, diagnostics, features, groups, certificates, timings, code and audit as
witness-preference-001. Synthetic analytic weighted/unweighted fits, finite-difference
gradient checks, constant/tie cases and invalid-input checks precede the freeze.
