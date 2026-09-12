# Fixed-group regret variants 001

Development comparison on the 16 retained size-confirmation incumbent cases.
Both roles train from zero against unrestricted hand-specific best responses.
No grouping repair, changed game, fresh boards, or fitted hyperparameters.

## Results

| Recipe | Final residual | Final exploitability | 50k solver seconds |
|---|---:|---:|---:|
| rm | 0.000372076 | 0.020753231 | 3.006 |
| rm_plus | 0.000787682 | 0.021168837 | 3.061 |
| discounted | 0.000522655 | 0.020903810 | 3.206 |

Values are chips; residual is exploitability minus the certified floor lower bound.
Times are mean across cases of the median of two timed repetitions.

| Recipe | Target 0.001 first/persistent | Target 0.0001 first/persistent |
|---|---:|---:|
| rm | 16/16 of 16 | 0/0 of 16 |
| rm_plus | 12/12 of 16 | 0/0 of 16 |
| discounted | 14/14 of 16 | 0/0 of 16 |

Persistent means that this and all subsequent sampled checkpoints pass.
It does not assert monotonic convergence between checkpoints or after 50,000 updates.

## Frozen decision rule

- rm_plus: earns fresh-board confirmation = False;
  paired crossings 12/16; faster 1/16;
  median paired solver-time ratio 2.3128;
  mean final residual nonworse = False.
- discounted: earns fresh-board confirmation = False;
  paired crossings 14/16; faster 2/16;
  median paired solver-time ratio 1.0732;
  mean final residual nonworse = False.

The predeclared rule requires all 16 paired persistent crossings, at least 12 faster
cases, median paired ratio below one, and no worse mean final residual.

## Cases: final remaining error

| Case | Texture | Range | rm | rm_plus | discounted |
|---|---|---|---:|---:|---:|
| 0 | unpaired-no-flush | uniform | 0.00022164 | 0.00036664 | 0.00028096 |
| 1 | unpaired-no-flush | polarized | 0.00047060 | 0.00094487 | 0.00059017 |
| 2 | unpaired-no-flush | uniform | 0.00020458 | 0.00037720 | 0.00025055 |
| 3 | unpaired-no-flush | polarized | 0.00044545 | 0.00079455 | 0.00052244 |
| 4 | unpaired-flush-possible | uniform | 0.00020722 | 0.00038177 | 0.00024618 |
| 5 | unpaired-flush-possible | polarized | 0.00017849 | 0.00058821 | 0.00041816 |
| 6 | unpaired-flush-possible | uniform | 0.00030669 | 0.00086530 | 0.00057758 |
| 7 | unpaired-flush-possible | polarized | 0.00045900 | 0.00161728 | 0.00102122 |
| 8 | one-pair | uniform | 0.00023039 | 0.00041519 | 0.00029849 |
| 9 | one-pair | polarized | 0.00045777 | 0.00091151 | 0.00059597 |
| 10 | one-pair | uniform | 0.00022692 | 0.00037118 | 0.00020466 |
| 11 | one-pair | polarized | 0.00071339 | 0.00120135 | 0.00089774 |
| 12 | multiple-pairs-or-trips | uniform | 0.00020191 | 0.00031864 | 0.00021921 |
| 13 | multiple-pairs-or-trips | polarized | 0.00042342 | 0.00110822 | 0.00063837 |
| 14 | multiple-pairs-or-trips | uniform | 0.00049475 | 0.00083555 | 0.00034928 |
| 15 | multiple-pairs-or-trips | polarized | 0.00071098 | 0.00150545 | 0.00125150 |

## Interpretation limits

rm uses signed cumulative regret and uniform averaging. rm_plus clips regret AFTER updates
and uses quadratic averaging. discounted uses (alpha,beta,gamma)=(1.5,0,2), also with
quadratic averaging. Recipe changes bundle averaging and regret; no causal attribution
to either component alone. These adapt published recipes to the existing best-response
learner, not a new full CFR self-play implementation or a transferred convergence theorem.

The floor has an exact verified interval [L,U]. Every checkpoint retains [E-U,E-L].
Thresholds use the conservative upper residual E-L, with no tolerance or clipping.
Known boards are a development panel; no unseen-board or six-max playing-strength claim.

## Timing

Five checkpoints: 500, 2000, 10000, 25000, 50000. Arm order rotates by case and reverses
in repetition two. Policies match exactly across repetitions. Solver time includes setup,
updates and materializing averages. Exact scoring is excluded and separately timed on
repetition one; summary crossing records include cumulative scoring for that pass.
Two timing observations describe a range, not a confidence interval. Budget summaries use
the latest completed checkpoint, never interpolation or the retrospectively best policy.
A missing first checkpoint remains missing; no conditional mean is shown as complete.
Shared game reconstruction, existing certificate validation and audit replay are outside
solver timings. Exact checkpoint monitoring is research instrumentation, not live latency.

## Verification and retention

Eight analytic checks; three independent small-game replay comparisons before freezing.
96 timed trajectories (4.8 million updates); 48 exact repeat-identity checks.
2.4 million updates replayed using frozen payoff code and independent update transforms.
240 exact profiles and 32 asymmetric certificates reverified; no new LP solves.
All 16 plain 50k policies equal the historical checkpoints exactly.
All 31 prior milestone manifests and their members remain unchanged.
Python 3.14.6; one BLAS thread; no allocation tracing; 900-second per-phase timeout.
No hard RSS cap. Production source, frozen repair baseline and existing evidence unchanged.
Run plus verification: 605.671 seconds; exit 0.

Full curves, threshold crossings, timing samples and subgroup summaries: `summary.json`.
Raw policies and exact rational certificates remain in each retained case file.

Recipe reference: https://arxiv.org/pdf/1809.04040 (Brown and Sandholm, 2019).

Plan SHA-256: 954f02a1ad7de5f3ff3bb47e6b00424ba924cf7da0cfac5fc44a3f00dae16799

Results manifest SHA-256: 847bbe30c0baa4db2c781c90605c5542b00386dc387cd6f67edfa1f5b653c3dd
