# Boundary-resolution intervention

The user requested: "Design and run the next test". This authorizes the bounded
decision-focused experiment below, including preparation, execution and retention,
not commit, push or deployment. This is a post-result diagnostic on observed boards.

Question: does suppressing differences between large same-sign advantages improve
grouping, and is the answer different with exact versus predicted features?

Use all 48 observed witness-distillation-001 cases, eight boards x three pools x two
range regimes, 96 holdings per seat. Freeze one transform, f(x)=min(0.5,max(-0.5,x)),
on all four witness columns. The threshold comes from the preceding diagnostic's
fixed 0.5-chip band, not a search over outcomes. Apply it to exact witness advantages
and saved predicted advantages separately. Do not combine inputs, refit, tune or
select a threshold. Positive/negative/zero signs are preserved; magnitudes inside
the band are unchanged; larger same-sign values coincide. That can discard useful
information as well as focus distance near zero. Either outcome is informative.

New methods: clipped_oracle and clipped_prediction. Each uses the same anchored
clustering, own-hand weights and occupied group counts as its unmodified reference.
Anchors keep exactly K occupied groups even if clipping creates duplicate vectors;
the resulting within-tie allocation is part of this algorithm, not a claim of unique
or optimal grouping. Retain ties and all resulting groups/certificates.

Paired contrasts: clipped_oracle minus direct_witness; clipped_prediction minus
predicted_only. Also report both against existing range_response, range_equity,
uniform_equity, full-hand and each other. Equal-case means equal eight-board means
in this balanced panel. Report every board/pool/regime/texture and leave-one-board-out
summary, all regressions and overlaps. No p-values, board population claim or BB/100.
The oracle arm uses solved witness information and is a diagnostic, not a cheap
deployable representation. An oracle gain alone does not validate the learned model.

Reconstruct every game/input and reproduce saved predictions from the fixed model.
Recompute exact witness advantages from retained witness policies and require exact
agreement with the saved feature arrays. The predicted arm cannot consume oracle
features. Record both clipped arrays for independent scalar clipping verification.
Reuse six prior certified floors unchanged; solve only the two new methods: 192 LP
calls. Count calls and require exactly 192. No model fitting is allowed.

One Python 3.14.6 worker, NumPy 2.5.2, SciPy 1.18.0, one BLAS thread, 600-second
worker limit and existing per-LP five-second/10,000-iteration limits. No RSS cap.
The parent repeats feature/group construction and verifies all certificates with
optimization disabled, then produces the summary. Parent work is outside the worker
limit. Timing spans worker launch through parent verification and manifest writing,
excluding preflight, output reservation and final receipt writing. No automatic retry.

Reuse the previous standalone experiment machinery by a recorded source diff, leaving
all prior files unchanged. Before scoring, synthetic checks cover clipping signs,
endpoints, interior identity, saturation, idempotence, refusal of nonfinite/wrong shape,
arm separation and exact occupied capacity under ties. Afterward, independent scalar
clipping and exact-rational floor/difference/aggregate checks audit retained results.
Preserve every prior milestone; retain this outcome as witness-boundary-001. No new
cold-review claim or publication is part of this standalone research intervention.
