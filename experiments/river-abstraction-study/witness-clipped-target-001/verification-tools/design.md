# Clipped-target learning experiment

User authority: "Please design and run the test", approving the preceding controlled
proposal. One new trained candidate on the observed panel; no commit, push or adoption.

Train the same two quadratic ridge models using the original 48 witness-pilot cases.
Keep the eleven inputs, 78-column quadratic basis, four outputs, float64, lambda=.001,
unpenalized intercept and equal-case/own-hand weighting exactly as before. Change only
the target array to clip(exact witness advantage,-0.5,+0.5) before calling fit_model.
No hyperparameter search, standardization, feature changes, early stopping or new board.
The model wrapper records the changed target semantics even though the inherited
coefficient schema and predictor API remain unchanged. No deployed caller is changed.

Reconstruct every training game and raw feature, recompute exact targets from retained
witness policies and reproduce the old model's predictions. Require equality with
sealed records. Fit two models and save them before any evaluation case computation.
The parent independently reconstructs training and refits both models, requiring
identical coefficients and diagnostic records. The two parent verification fits are
not a model search. The independent scalar audit adds no fits or LPs.

Evaluate all 48 observed cases used in witness-boundary-001. Predict with the new
model, clip the predictions to the same [-0.5,+0.5] range, and cluster those four
features with unchanged anchored_clusters, own-hand weights and occupied capacity.
No oracle features enter candidate group formation. Exact targets enter only the
separately retained prediction-error diagnostics and existing oracle references.

Primary contrast: new clipped-target model floor minus prior clipped_prediction
floor (old model trained on full targets, clipped afterward). Key references are
range_response and clipped_oracle; report all eight retained boundary-method floors.
Only one new grouping method: 96 new LP calls, with existing five-second and 10,000-
iteration limits. Record actual calls and require exactly 96. No control re-solves.

Report equal-board means (eight boards, three pools, two regimes), signed numerical
interval comparisons, counts, all board/pool/regime/texture/leave-one-board-out values,
and the two preidentified b07-p1-polarized / b07-p2-polarized cases without excluding
them. Prediction diagnostics compare old and new clipped features against clipped
exact targets on both training and evaluation. Weighted per-column MSE and MAE are
secondary, not substitutes for grouping floor. No success threshold is chosen later.

This is an intervention on observed data. Improved diagnostics without improved
strategic floor is a negative strategic result. Improvement on this panel makes a
candidate for fresh-board confirmation, not a generalization or six-max strength claim.
Holding lambda fixed is intentional; changing target scale can change the relative
influence of the same regularizer. This test does not isolate that effect separately.

One Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0 worker, one BLAS thread, 600-second
worker limit; parent verification outside it, no RSS cap. Retain worker and worker-
plus-parent time with the same explicit boundary as the prior standalone runner.
Fresh exclusive output, no automatic retry, preserve failures. Reuse unchanged
execution/summary mechanics through a retained source diff; no production source edits.

Before execution: inherited clipping/capacity checks plus an analytic intercept-only
example distinguishing clipping targets before fitting from clipping predictions
afterward, checking equal case weight despite unequal row counts. After execution:
scalar clipping/error checks, regularized normal-equation residual checks from saved
training inputs, and exact-rational certificate/comparison/aggregate verification.
Retain full models, predictions, all cases and failures/nonimprovements as
witness-clipped-target-001, preserving every previous milestone.
