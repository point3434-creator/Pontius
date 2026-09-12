# Reserved-board witness distillation: witness-distillation-001

One approved invocation completed all 48 cases on eight newly reserved boards,
three hand pools and two range regimes, with 96 holdings per seat. Two fixed
quadratic ridge models were trained on the 48 observed witness-pilot cases.
There was no retry, parameter tuning, changed panel or omitted result.

## Research disposition

Do not adopt this fixed predictor as an improvement. Its mean floor is 86.14% higher
than range-equity grouping and 108.11% higher than range-response grouping. It is worse
on every board mean against both range controls. Every leave-one-board-out primary
mean remains positive. This is a consistent failure on this panel, not one bad board.

Direct witness grouping remains useful on these same new boards: mean floor 0.002260272,
versus range equity 0.005736919 and range response 0.005131337. Direct witness grouping
improves 44 of 48 cases against range equity and 46 of 48 against range response.
The strategic target's value survives this additional panel; this fixed transformation
of eleven existing features does not recover that benefit.

The experiment does not distinguish insufficient input information, model capacity,
training-board coverage, regularization, and mismatch between squared prediction error
and strategically useful grouping. No causal attribution among these is established.
Fitting was cheap, but speed without useful grouping quality does not justify adoption.

The next useful diagnostic is to compare this frozen model's errors on observed training
cases with its errors on these now-observed evaluation cases, including behavior near
action indifference. Establish fit failure versus transfer failure before choosing a
larger predictor or more training boards. This is a recommendation, not another launch.
Any subsequently tuned candidate needs new reserved evidence for a generalization claim.

## Strategic results

Lower floor is better. This is the minimum full-hand exploitability achievable
with these groups in the conditional one-bet heads-up river game. It is not a
trained-policy win rate or BB/100. Values are midpoints of retained certified
numerical intervals in game chips. All compressed methods match occupied capacity.
The mean weights eight boards equally, with equal pools and regimes within each.

| Method | Mean floor | Predicted lower / higher / overlapping |
|---|---:|---:|
| exact | 0.0000000000 | 0/48/0 |
| predicted_witness | 0.0106785993 | - |
| range_equity | 0.0057369186 | 6/41/1 |
| range_response | 0.0051313371 | 5/43/0 |
| uniform_equity_200 | 0.0082456964 | 15/33/0 |
| Direct witness grouping | 0.0022602721 | 2/46/0 |

Primary comparison: predicted minus range-equity floor. Secondary: range-response
and the gap to direct witness grouping. Positive differences are worse.

Mean predicted-minus-oracle gap: 0.0084183273 chips.
Neither clustering method globally optimizes partitions, so predicted groups can
beat direct witness groups in individual cases without invalidating the comparison.

## Board sensitivity

| Board | Cards | Predicted | Delta range equity | Delta range response |
|---|---|---:|---:|---:|
| 0 | 2d 3h 4d 5s Kh | 0.006347832 | 0.002865557 | 0.003106078 |
| 1 | 3d 4d 9s Ts Ac | 0.008567855 | 0.003943305 | 0.005489642 |
| 2 | 4s 5h 9s Js Ad | 0.004348381 | 0.001486202 | 0.002776904 |
| 3 | 2s 8h 9s Qd Ks | 0.008221313 | 0.004264189 | 0.005153618 |
| 4 | 3c Th Jd Js Kd | 0.010742264 | 0.001387329 | 0.001813646 |
| 5 | 9d Jd Jh Qh Ad | 0.017353921 | 0.012561387 | 0.013791386 |
| 6 | 5h 5s 9c Kh Ks | 0.015005314 | 0.006515888 | 0.006057785 |
| 7 | 6h 6s Jh Qc Qd | 0.014841914 | 0.006509589 | 0.006189040 |

Leave-one-board-out primary means: 0.003853151 to 0.005449445 chips.
These are descriptive sensitivity checks, not confidence intervals or a natural-board
sampling claim. Pool replicates and holdings do not create additional independent boards.

## Range regimes

| Regime | Predicted | Range equity | Range response | Lower / higher / overlap vs equity |
|---|---:|---:|---:|---:|
| polarized | 0.011693584 | 0.005602446 | 0.004064202 | 4/20/0 |
| uniform | 0.009663615 | 0.005871391 | 0.006198472 | 2/21/1 |

## Every primary nonimprovement

All cases whose primary interval is not wholly negative are retained below.
The complete artifact also retains comparisons against every other method.

| Case | Delta range equity | Delta range response | Delta direct witness |
|---|---:|---:|---:|
| b00-p0-uniform | 0.001749044 | 0.001126145 | 0.003979407 |
| b00-p0-polarized | 0.000411815 | 0.001750673 | 0.003129798 |
| b00-p1-uniform | 0.004832708 | 0.003159291 | 0.006947355 |
| b00-p1-polarized | 0.007102607 | 0.008132221 | 0.011278321 |
| b00-p2-uniform | 0.001605484 | 0.001160486 | 0.003826383 |
| b00-p2-polarized | 0.001491685 | 0.003307650 | 0.004950666 |
| b01-p0-uniform | 0.007120817 | 0.009463516 | 0.011136166 |
| b01-p1-uniform | 0.008832901 | 0.010802824 | 0.014692747 |
| b01-p1-polarized | 0.000381505 | 0.001589603 | 0.004498199 |
| b01-p2-uniform | 0.005724310 | 0.004760400 | 0.008008436 |
| b01-p2-polarized | 0.003491009 | 0.005071037 | 0.005729255 |
| b02-p0-uniform | -0.000000000 | 0.001919669 | 0.004708932 |
| b02-p0-polarized | 0.002373033 | 0.002552506 | 0.003748993 |
| b02-p1-uniform | 0.002693682 | 0.002065430 | 0.003081857 |
| b02-p1-polarized | 0.000218398 | 0.003494365 | -0.000359341 |
| b02-p2-uniform | 0.004973610 | 0.005365998 | 0.007058170 |
| b03-p0-uniform | 0.012099518 | 0.010881916 | 0.013851878 |
| b03-p0-polarized | 0.001521789 | 0.002466728 | 0.006171701 |
| b03-p1-uniform | 0.000669802 | 0.000471342 | 0.004422915 |
| b03-p1-polarized | 0.001660936 | 0.002740545 | 0.003155779 |
| b03-p2-uniform | 0.006250246 | 0.007121075 | 0.010103998 |
| b03-p2-polarized | 0.003382838 | 0.007240099 | 0.008745875 |
| b04-p0-uniform | 0.003414037 | 0.002842162 | 0.004719097 |
| b04-p0-polarized | 0.001840770 | 0.003480737 | 0.009885221 |
| b04-p1-uniform | 0.002557398 | -0.000875765 | 0.006159134 |
| b04-p2-polarized | 0.005247369 | 0.007161796 | 0.017135799 |
| b05-p0-uniform | 0.003083894 | 0.005170050 | 0.009428389 |
| b05-p0-polarized | 0.015553203 | 0.014584804 | 0.016572571 |
| b05-p1-polarized | 0.036797530 | 0.038883165 | 0.039641578 |
| b05-p2-uniform | 0.003319672 | 0.005084567 | 0.008136018 |
| b05-p2-polarized | 0.018408744 | 0.019012001 | 0.021244055 |
| b06-p0-uniform | 0.004183870 | 0.000439217 | 0.010231420 |
| b06-p0-polarized | 0.008196244 | 0.015023154 | 0.016341415 |
| b06-p1-uniform | 0.004054054 | -0.000885453 | 0.002871397 |
| b06-p1-polarized | 0.011926958 | 0.013042000 | 0.016459409 |
| b06-p2-uniform | 0.006812852 | 0.002471096 | 0.005882961 |
| b06-p2-polarized | 0.003921347 | 0.006256697 | 0.008106694 |
| b07-p0-uniform | 0.002866791 | 0.003073400 | 0.004965181 |
| b07-p0-polarized | 0.010986547 | 0.009329846 | 0.017255605 |
| b07-p1-uniform | 0.005140368 | 0.004508157 | 0.008351674 |
| b07-p2-uniform | 0.003372307 | 0.004010761 | 0.005857161 |
| b07-p2-polarized | 0.018923823 | 0.020926779 | 0.025391290 |

## Prediction diagnostics

Per-column errors are equally averaged over all 48 cases; each case MSE is weighted
by the seat's own-hand marginal. Maximum absolute error is over the entire panel.
Column order is exact, uniform-equity, range-equity, range-response witness.
These diagnostics do not replace the certified strategic endpoint.

| Seat | Column | Mean weighted MSE | Maximum absolute error |
|---|---:|---:|---:|
| 0 | 0 | 0.148751334 | 2.218790878 |
| 0 | 1 | 0.161105378 | 2.419847185 |
| 0 | 2 | 0.156432828 | 2.320950207 |
| 0 | 3 | 0.145973257 | 2.435247871 |
| 1 | 0 | 0.454661697 | 3.970629408 |
| 1 | 1 | 0.495961747 | 4.139656687 |
| 1 | 2 | 0.468525099 | 4.152815362 |
| 1 | 3 | 0.454039788 | 4.109308742 |

## Measured cost and verification

| Boundary or component | Seconds |
|---|---:|
| Whole inner command through exit | 429.408330 |
| Worker receipt | 292.570225 |
| Worker training reconstruction/verification | 62.178696 |
| Worker fitting | 0.026006 |
| New-board uniform-equity preparation | 2.734225 |
| game_and_control_preparation | 5.240793 |
| oracle_rebuild_and_solve | 189.474124 |
| prediction_and_clustering | 1.039674 |
| student_solve_and_verification | 30.167774 |

Whole-command time includes startup, worker, parent independent refit/reconstruction,
verification, summary/manifest writing and exit. It excludes outer-recorder preflight
and final receipt writing. Subtraction is not a pure parent-cost measurement.
Historical training-label generation cost is excluded and remains in witness-pilot-001.
Prediction/clustering timing does not include all feature/equity/game preparation.
This is not a matched end-to-end speed benchmark or an online latency guarantee.

Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one worker and one BLAS thread.
The worker limit was 1,200 seconds, parent work outside that limit. No RSS cap
or peak-memory measurement is claimed. Both inner and outer commands exited zero.

The frozen parent independently refitted both models and required canonical equality,
then reconstructed every new game, teacher, predicted group, certificate and comparison.
The separate stdlib audit checked 288 floor identities, 576 asymmetric gap records,
432 case comparisons, both panels' aggregates, oracle gaps and retained identity.
It added no LP calls or model fits. Maximum asymmetric certificate width:
1.724198e-15 chips. These are numerical bounds on
binary64 payoff coefficients, not sampling uncertainty or an independent card-evaluator proof.

## Retention and authority

Original output: D:/Pontius-training/river-abstraction-study/witness-distillation-001
Repository milestone: experiments/river-abstraction-study/witness-distillation-001
Both fitted models, all cases, summary, original manifest, authorization and outer
timing records are retained together. All five earlier milestones remain unchanged.
No commit or push was performed. The eight evaluation boards are now observed data.

Plan SHA-256:
47b26fc64aa3b2ddb36ebe11a02d16253b240a61672cff162c51af689728e524

Original result manifest SHA-256:
a738c67dc5f14506123b72daff3af91462b5faaca7c14c38ae19c9f1f589c9fc
