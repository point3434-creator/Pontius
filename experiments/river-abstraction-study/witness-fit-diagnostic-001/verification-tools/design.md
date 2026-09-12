# Frozen-model fit versus transfer diagnostic

Authorization: the user's "Let's design and run the next test" follows the proposed
comparison of frozen-model errors on observed training and evaluation cases.
This authorizes this diagnostic preparation and invocation, not commit or push.

Use witness-pilot-001's 48 training cases and witness-distillation-001's 48 evaluation
cases, all now observed. Preserve both complete milestones and the fitted model bytes.
No new board, fit, parameter change, LP, grouping score or candidate selection.

Reconstruct each game/input and the eleven raw features using the frozen source.
Require reconstructed inputs to match retained inputs; use retained witness targets.
Require evaluation predictions to equal the saved predictions exactly. Patch fitting
and solver entry points to raise. Read-only input hashes are checked before and after.

Report per seat and four witness columns: weighted MSE, MAE, bias, and model MSE
relative to a constant equal to the training target mean. Case weights are equal;
within each case use normalized own-hand marginals. The diagnostic constant is not
a refit of the saved model. All 48 cases per split give equal board/regime/pool weight.

Report target SD, predicted SD and weighted correlation to distinguish amplitude
compression from a complete loss of association, without assigning a causal mechanism.
Report sign mismatch excluding abs(target)<=1e-10 from its conditional denominator.
Predicted zero selects the passive action. Also report the unconditional opportunity
cost max(target,0)-target*I(prediction>0). This compares a binary response to each
particular fixed witness, not a shared policy, exploitability or realized chip winnings.

Fixed target-magnitude bands, in game chips: [0,0.1], (0.1,0.5], (0.5,infinity).
For each band report weight mass, conditional MSE, mismatch and opportunity cost.
These descriptive bands are not chosen from new diagnostic outcomes. No p-values,
independent-hand sample-size claim, population inference or automatic next run.

Overall, board and range-regime summaries retain both splits separately. Training
and evaluation panels differ in board content, so their error difference alone cannot
identify model underfit, overfit, information insufficiency or distribution shift.

Verification: analytic weighted/sign/tie/band checks before execution, then independent
scalar recomputation of every summary metric from retained per-hand arrays. No optimizer
or additional prediction pass is required for the scalar audit. Save negative outcomes.

One sequential Python 3.14.6 worker with NumPy 2.5.2 and SciPy 1.18.0, BLAS threads 1.
300-second worker timeout; no RSS cap. The worker performs all diagnostic computations
and writes a results manifest. The parent retains child captures, exit and elapsed time;
requires successful exit and verifies that manifest. There is no automatic retry.
The timer spans child execution through exit, excludes parent preflight and final audit.
Prior-source and experiment milestones remain unchanged. Standalone diagnostic artifacts
are retained as a new milestone; no production module or shared runner is modified.
