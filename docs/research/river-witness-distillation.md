# Fixed witness-feature distillation on reserved boards

This bounded research extension asks whether a fixed inexpensive feature predictor
can preserve useful grouping quality on unseen boards without computing test-case
opponent witnesses to construct its groups. The user approved proceeding with the
learned-feature comparison. Build/review is authorized; the actual bound training
and evaluation invocation requires a separate one-shot approval. No commit or push.

## Fixed training and evaluation populations

Train only on the 48 complete cases of witness-pilot-001: eight observed boards,
three hand-pool replicates and two regimes, 96 holdings per seat. Bind the exact
milestone manifest d3b52b5f3c6046c6c36f2c967fa6d9e5e6f43608465da2cc974f94e54a121032
and producer plan 535a3fa5b4d55d8bc6cc29763c63b5ab41f89cf0ea190bca90f9c00a5a8c9d2c.
Every archive member is checked; every training case is reconstructed and its
teacher certificates/features verified before fitting. Prior data are read-only.

Reserve eight new boards by the same first-two-per-texture selection procedure
in river-witness-pilot.md, with board seed river-witness-distillation-001. Exclude
all suit-equivalent versions of the four original development/holdout boards,
the eight witness-pilot boards, and already selected new boards. Use the inherited
four disjoint texture bins and 10,000-attempt bound. No outcome influences selection.
Use the inherited pilot.hand_pool recipe unchanged (including its original seed
domain); new board identities create new draws. For each new board use three
96-holding pools per seat and uniform/polarized regimes sharing those holdings.
Full evaluation: 48 cases, eight board-level units, balanced across four textures.
No board, seed, model, feature or hyperparameter changes after observing results.

Plan generation hashes training data and selects board/hand-pool recipes only.
It does not fit the actual training set, evaluate reserved-board equities, produce
reserved groups or call an LP. Build checks use synthetic regression data and
two-hand fixtures on the first two original development boards. Smoke training
uses the first old board, smoke evaluation the second; smoke is not evidence of
generalization or resource feasibility of the full 96-hand invocation.

## Candidate and its precise information budget

Use one quadratic ridge regressor per seat, with four outputs in the unchanged
exact/uniform_equity_200/range_equity/range_response witness order. Targets are
the existing witness action-advantage features, preserving their signs, chip units,
own-hand normalization and caller bet reach. Never substitute action frequencies.

Each hand's input has eleven probability-valued features: the nine existing
range-response columns (conditional opponent mass, win mass and tie mass in each
of three opponent uniform-equity bands), followed by range equity and uniform
equity. These use the same public board and known ranges as the existing controls.
They contain no evaluated test-case witness, solved policy, teacher target or
cluster label. No raw-card/text embeddings, board-specific lookup, neural network,
history features or new strategic information are introduced. This tests a learned
nonlinear transformation of existing information, not a general-purpose embedding.

Polynomial basis: intercept, the eleven raw columns in their stated order, then
x_i*x_j for i=0..10 and j=i..10, in that order. This gives 78 columns. No standardizing,
whitening, clipping or data-dependent feature selection. Inputs must be finite and
in [0,1] within 1e-12 floating tolerance. Outputs are finite real chip predictions;
they are not clipped to target bounds. Both models use float64 and fixed lambda=.001.

For each seat minimize sum_c sum_h (mu_ch/48)*||phi(x_ch) B-y_ch||^2
+ .001*||B_nonintercept||^2. Each case's own-hand marginal mu sums to one. All
48 cases get equal total weight, hence all eight training boards get equal weight.
Fit via the single regularized normal-equation solve in the pinned NumPy runtime.
The intercept is not penalized. There is no tuning grid, validation selection,
early stopping, multiple starts, retry or evaluation-driven model choice.

Cluster the four predicted values using unchanged anchored_clusters, existing
own-hand marginal weights and exact occupied capacity per seat of that case's
uniform_equity_200 control. No exact-witness fallback is used on any hand/case.
The predicted groups are formed before new-case witness solutions are computed.
Models are written before any evaluation-board equity preparation. The test-case
oracle is used solely afterward for evaluation and feature-error measurement.

## Controls, endpoints and accounting

Evaluate all four old controls, exact-witness grouping and predicted-witness
grouping on each new case. Ten LP calls produce the four controls plus oracle;
two more certify predicted grouping. Total: 576 new LP calls. Fitting and training
certificate verification invoke no optimizer. Training labels' historical creation
cost belongs to witness-pilot-001; it is not zero and is excluded from new worker time.

Primary endpoint: predicted grouping floor minus range_equity grouping floor,
averaged equally across eight boards, each averaging pools and regimes. Secondary:
range_response and predicted-minus-oracle gap. Retain all other control comparisons.
Use exact rational interval arithmetic on the existing binary64 payoff coefficients;
classify improvement/regression only when the entire difference interval has a sign.
No acceptance threshold or meaningful-effect margin is selected post hoc.

Report all cases, all regressions, board means, pool means and descriptive SDs,
regime/texture breakdowns and leave-one-board-out results using the inherited pilot
aggregation. Keep the oracle results beside the student results. Report weighted
per-column feature MSE and maximum absolute errors for both seats for every case.
Prediction accuracy is diagnostic, never a substitute for strategic grouping floor.
Do not headline a gain-capture percentage when oracle gain is zero or changes sign;
retain absolute floor differences. Student groups can beat oracle groups because
neither clustering heuristic globally optimizes the partition.

Timing categories: verified training-data reconstruction, model fitting, new-board
uniform-equity preparation, game/control preparation, prediction plus clustering,
oracle rebuilding plus solving, and student solving plus verification. The oracle
path reconstructs its inputs again; that cost is included in its named category.
Prediction re-executed during verification is included in verification time. No
category is allocation-traced. Report worker and whole-invocation wall times too.
The input features still require equity/range calculations and an exact joint game
in this lab; no claim of cheap full-game deployment or an online latency bound follows.

Eight selected boards are the board-level units, not 48 independent boards or
9,216 independent training examples. This balanced pilot makes no natural-board
frequency, all-board significance, six-max, BB/100 or equal-compute claim. Both
regimes and all pools remain included. Missing/failing cases preclude completion.

## Execution, verification and retention

Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, one sequential worker and one BLAS thread.
Worker timeout: 1,200 seconds including training validation and fitting, evaluation
preparation and all 576 LP calls. Each LP retains five seconds and 10,000 iterations.
Parent reconstruction, refitting, validation and I/O are outside the worker timeout.
No process RSS cap or measured peak-memory guarantee. These are stop bounds only.

Reserve a fresh output directory atomically; retain plan/start, fitted models,
timings, captures/receipt, each case, summary and manifest. The parent reloads and
reverifies the pinned training data, refits both models and demands identical model
bytes under canonical JSON. It independently reconstructs every new case, teacher,
predicted feature/group, certificate and comparison with no additional LP calls.
Source/data hashes are rechecked before completion. Worker success alone is
insufficient: successful parent exit and valid final manifest are required.

Failure, timeout, corrupt model, missing result, source/data drift or evidence-write
error prevents success and retains failure evidence; no automatic retry. Hard kill,
power loss and hostile concurrent mutation remain outside the inherited recovery
contract. The internal worker entry is not an authorization interface. Preserve all
five prior milestones and all old computational source. One opposing review then
separate bound-run approval; no experiment has been launched by this specification.
