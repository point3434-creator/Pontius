# Experiment Results

This file records compact, reviewable conclusions. Raw JSON artifacts under
`experiments/results/` are generated locally and excluded from version control
until a checkpoint package explicitly promotes them.

## EXP-0001: CFR versus LCFR on two-player Kuhn

**Date:** 2026-08-18

**Status:** Observed; reference verification, not a general algorithm claim.

**Configuration:** 20,000 alternating full-tree iterations, average policy,
exact pure-information-set best responses, sequential wall-clock runs.

| Solver | Solver seconds | Player-0 value | NashConv | Exploitability |
|---|---:|---:|---:|---:|
| CFR | 3.911 | -0.05555956 | 0.00014427 | 0.00007213 |
| LCFR | 3.917 | -0.05555555 | 0.00000859 | 0.00000430 |

The analytical player-0 game value is `-1/18 = -0.05555556`. At this iteration
budget LCFR produced approximately 16.8 times lower NashConv for essentially
the same reference-runtime cost. The current strategies were materially less
stable than the averages: current-policy NashConv was approximately `0.05890`
for CFR and `0.00487` for LCFR.

**Interpretation:** LCFR passes as the initial control and earned advancement to
multiplayer and perturbed-leaf tests. This does not establish that LCFR is best
for sampled, warm-started, dynamic, or six-player searches.

**Reproduction:**

```powershell
$env:PYTHONPATH = "src"
python -m pontius.experiment --config experiments/configs/kuhn2-cfr-20000.json
python -m pontius.experiment --config experiments/configs/kuhn2-lcfr-20000.json
```

## EXP-0002: CFR versus LCFR on three-player Kuhn

**Date:** 2026-08-18

**Status:** Observed; first multiplayer control, not a convergence claim.

**Configuration:** 5,000 alternating full-tree iterations, average policy,
exact dynamic perfect-recall best responses, sequential wall-clock runs.

| Solver | Solver seconds | Utilities `(p0, p1, p2)` | NashConv |
|---|---:|---|---:|
| CFR | 27.401 | `(-0.0288924, -0.0208050, 0.0496974)` | 0.00077954 |
| LCFR | 25.439 | `(-0.0262542, -0.0208298, 0.0470839)` | 0.00001229 |

At this budget LCFR produced approximately 63.4 times lower NashConv. The
single-run timing difference is not promoted as a speed result. The differing
utility profiles are compatible with multiplayer equilibrium nonuniqueness and
demonstrate why utility alone cannot rank solver quality. Current-policy
NashConv remained higher than average-policy NashConv: approximately `0.05554`
for CFR and `0.00736` for LCFR.

**Validation:** the dynamic best response exactly matches exhaustive pure-policy
enumeration for two-player uniform and passive profiles. In three-player Kuhn,
its returned response is undominated by every single-information-set action
change. A fully independent sequence-form three-player cross-check remains
future work.

## EXP-0003: Exact evaluator scaling on uniform Kuhn profiles

**Date:** 2026-08-18

**Status:** Observed hardware boundary.

**Measurement:** expected utilities and exact dynamic best responses for every
player, one sequential run per player count.

| Players | Evaluation seconds | Uniform-profile NashConv |
|---:|---:|---:|
| 2 | 0.001 | 0.916666667 |
| 3 | 0.014 | 2.062500000 |
| 4 | 0.249 | 3.476041667 |
| 5 | 4.940 | 5.010807292 |
| 6 | 106.623 | 6.631305804 |

Exact six-player evaluation is practical as an occasional checkpoint in this
toy game but already too costly for frequent training reports. The growth is a
design constraint for checkpoint C2: evaluation cadence must be decoupled from
solver iterations, and later games require restricted or incremental deviation
evaluators.

## EXP-0004: Four CFR update rules

**Date:** 2026-08-18

**Status:** Observed; fixed exact games with exact leaves and cold starts.

All variants use the same alternating full-tree traversal. CFR+ means RM+ with
quadratic averaging. DCFR means DCFR(1.5, 0, 2). Times are sequential solver
time and exclude exact evaluation.

### Two-player Kuhn, 20,000 iterations

| Solver | Seconds | NashConv at 2,000 | NashConv at 20,000 |
|---|---:|---:|---:|
| CFR | 6.188 | 1.07849e-3 | 1.44267e-4 |
| LCFR | 6.255 | **9.04947e-5** | **8.59435e-6** |
| CFR+ | 6.162 | 1.47866e-4 | 8.78964e-6 |
| DCFR | 6.180 | 1.83883e-4 | 2.36942e-5 |

LCFR and CFR+ are effectively tied at the final budget, with LCFR slightly
ahead in this run. Default DCFR does not win this game.

### Three-player Kuhn, 5,000 iterations

| Solver | Seconds | NashConv at 500 | NashConv at 1,000 | NashConv at 5,000 |
|---|---:|---:|---:|---:|
| CFR | 25.557 | 7.24304e-3 | 3.92234e-3 | 7.79538e-4 |
| LCFR | 25.626 | 3.78356e-4 | 1.50018e-4 | 1.23000e-5 |
| CFR+ | 26.013 | **1.36123e-5** | **6.49495e-6** | 1.22307e-6 |
| DCFR | 25.401 | 1.86172e-4 | 2.15893e-5 | **2.55287e-7** |

CFR+ is decisively best at the shortest measured budgets. DCFR overtakes it
between 1,000 and 2,500 iterations and finishes about 4.8 times below CFR+ and
48 times below LCFR. Current strategies remain less stable than averages, but
DCFR also has the best final current-policy NashConv (`2.47e-4`).

**Conclusion:** there is no justified global solver choice. CFR+ advances as
the short-budget control and DCFR as the longer-budget three-player control.
LCFR remains the Pluribus-style sampled/pruning candidate. The next experiments
must add warm starts, leaf perturbations, and tree changes before choosing an
online update rule.

## EXP-0005: Paired shallow-leaf sensitivity

**Date:** 2026-08-18

**Status:** Observed negative result; mechanism test, not a neural-leaf claim.

**Configuration:** two-player Kuhn; LCFR blueprint trained for 1,000 iterations;
blueprint NashConv `1.87060e-4`; search cut after one strategic action; 100
alternating iterations; average policy; precomputed exact blueprint
continuations; independent concrete-leaf zero-sum perturbations; five fixed
seeds. Each perturbed run is paired with an otherwise identical exact-leaf
control and both are evaluated in the original game.

### No blueprint prior, very small error

At leaf scale `0.001`, realized mean RMSE was `4.03756e-4`.

| Solver | Exact-control Δ NashConv from blueprint | Mean absolute causal Δ NashConv | Mean policy TV |
|---|---:|---:|---:|
| CFR | 8.62665e-2 | 1.83159e-2 | 0.13200 |
| LCFR | 8.77865e-2 | 1.93912e-2 | 0.13331 |
| CFR+ | 8.78167e-2 | 1.94126e-2 | 0.13333 |
| DCFR | 8.78167e-2 | 1.94126e-2 | 0.13333 |

The naïve shallow solve damaged a strong blueprint by roughly `0.087` NashConv
even with exact leaves, around 460 times the blueprint's initial NashConv. Tiny
leaf error then caused discontinuous policy changes. Some perturbations
accidentally improved the already poor exact control, so absolute causal change
is reported as sensitivity rather than called harm.

### Pseudo-regret warm start, mass 10

At leaf scale `0.01`, realized mean RMSE was `4.03756e-3`. Reference Python
search time was approximately 13.6-13.7 ms per 100-iteration arm and excludes
the precomputed leaf cost.

| Solver | Exact-control Δ NashConv | Mean causal Δ NashConv | Mean policy TV |
|---|---:|---:|---:|
| CFR | **1.18804e-4** | **5.98298e-4** | **1.47121e-3** |
| CFR+ | 1.78901e-4 | 9.53936e-4 | 2.20985e-3 |
| DCFR | 1.26431e-3 | 6.23371e-3 | 1.36085e-2 |
| LCFR | 7.70866e-3 | 3.11892e-2 | 7.34094e-2 |

The prior attenuated damage, but it did not make the exact control better than
the blueprint. CFR appears strongest here because it retains the prior; LCFR
and DCFR discount it. This is not evidence that CFR is the generally superior
online solver, and equal raw prior mass is not a solver-neutral comparison.

**Verdict:** reject unanchored shallow replacement as the current resolver.
Before spending on neural leaves, test a variant-neutral blueprint trust region,
residual/output interpolation, and a no-op acceptance option. Then add
reach-weighted and structured leaf errors. The tracked reproduction config is
`experiments/configs/leaf-kuhn2-initial-matrix.json`.

## EXP-0006: Blueprint-anchored depth-two search

**Date:** 2026-08-19

**Status:** Observed provisional advance; exact toy game only.

**Configuration:** two-player Kuhn; depth two, leaving six concrete
`check/bet` continuation leaves; 100 search iterations; precomputed blueprint
continuations; average policy unless stated. In-search anchoring constrains
behavior to `b * blueprint + (1 - b) * CFR candidate`. Output interpolation
blends only after an unanchored search. All candidates are evaluated in the
original full game, with blueprint/no-op retained.

### Blueprint strength and constraint location

| Blueprint iterations | Blueprint NashConv | Best output-only result | Best in-search result |
|---:|---:|---|---|
| 20 | 2.17100e-2 | Δ `-1.36555e-2`, output weight 1.0 | Δ `-1.77027e-2`, CFR+ anchor 0.50 |
| 100 | 2.17805e-3 | Δ `-1.97342e-4`, output weight 0.03 | Δ `-1.73541e-3`, CFR+ anchor 0.97 |
| 1,000 | 1.87060e-4 | no-op; every tested nonzero output weight worsened | Δ `-1.69448e-4`, LCFR anchor 0.99 |

Depth matters: unlike the one-action hybrid in EXP-0005, depth two includes an
opponent decision and can improve full-game NashConv. On the strong blueprint,
post-search interpolation merely hid an unsuitable unanchored policy; anchoring
the traversal itself produced a useful candidate.

### Exact leaves, strong blueprint, four update rules

The table selects each solver's best average among anchor weights 0.97, 0.99,
and 0.995. Times include solver initialization and 100 reference-Python
iterations, with leaves already materialized.

| Solver | Anchor | Average Δ NashConv | Current Δ NashConv | Search ms |
|---|---:|---:|---:|---:|
| CFR | 0.995 | -1.07842e-4 | +7.04390e-4 | 39.73 |
| CFR+ | 0.995 | -1.49818e-4 | +1.90342e-4 | 39.77 |
| DCFR | 0.990 | -1.57558e-4 | +4.43275e-4 | 39.43 |
| LCFR | 0.990 | **-1.69448e-4** | +1.55462e-4 | 39.05 |

Every current policy failed even though every selected average improved. LCFR
wins this exact-leaf slice, not the general solver decision.

### Leaf-error envelope

For a fixed CFR+ anchor of 0.995, ten deterministic error seeds produced:

| Realized leaf RMSE | Mean treatment Δ NashConv | Worst-seed Δ NashConv | Seeds improving blueprint |
|---:|---:|---:|---:|
| 4.62190e-5 | -1.53102e-4 | -1.35684e-4 | 10/10 |
| 1.38657e-4 | -1.46015e-4 | -1.25881e-4 | 10/10 |
| 4.62190e-4 | -6.40210e-5 | +5.21862e-6 | 9/10 |
| 1.38657e-3 | +3.22274e-4 | +5.91303e-4 | 2/10 |

At RMSE `4.62190e-4`, CFR+ anchor 0.99 had the best mean of the tested
solver/anchor pairs (`-6.94220e-5`), while LCFR 0.99 and DCFR 0.99 each improved
9/10 seeds with smaller worst failures. No candidate passed every seed. At RMSE
`1.38657e-3`, no-op was the correct mean decision.

**Verdict:** in-search anchoring creates a real but narrow strategy-quality
window. Advance anchored average policy as a control, not as a safety claim.
The result makes calibrated leaf uncertainty and no-op selection more valuable,
not less: computation should be spent only when the predicted improvement
margin exceeds leaf-error risk. Next add reach-weighted, correlated, biased, and
localized errors, then test a frozen selection rule on held-out multiplayer
games.

## EXP-0007: Structured and reach-weighted leaf error

**Date:** 2026-08-19

**Status:** Observed; measurement advance and scheduler falsification in one
tiny exact game.

**Configuration:** two-player Kuhn; 1,000-iteration LCFR blueprint with NashConv
`1.87060e-4`; depth-two anchored search for 100 iterations; six continuing
`check/bet` private-history leaves. Errors are measured uniformly, under joint
blueprint reach, and under each player's counterfactual reach. All treatment
policies are evaluated in the untouched full game.

### Same raw scale, different correlation

At random-error scale `1e-3`, 50 fixed seeds produced the following results.
The treatment column is NashConv change from the blueprint, so negative is
better. Because one coherent public-history draw does not average across the
six leaves, its mean realized root L2 was about 15% larger; the calibrated
control below separates that effect.

| Error grouping | Solver / anchor | Mean root L2 | Mean treatment Δ | Worst treatment Δ | Improving seeds |
|---|---|---:|---:|---:|---:|
| Concrete IID | LCFR / 0.990 | 2.127e-4 | -6.761e-5 | +8.175e-5 | 45/50 |
| Concrete IID | LCFR / 0.995 | 2.127e-4 | -4.157e-5 | +4.295e-4 | 40/50 |
| Concrete IID | CFR+ / 0.990 | 2.127e-4 | -6.627e-5 | +8.371e-5 | 41/50 |
| Concrete IID | CFR+ / 0.995 | 2.127e-4 | -5.969e-5 | +4.348e-4 | 44/50 |
| Public-history | LCFR / 0.990 | 2.450e-4 | -2.216e-5 | +2.871e-4 | 31/50 |
| Public-history | LCFR / 0.995 | 2.450e-4 | +2.393e-5 | +5.330e-4 | 31/50 |
| Public-history | CFR+ / 0.990 | 2.450e-4 | -5.541e-6 | +2.655e-4 | 28/50 |
| Public-history | CFR+ / 0.995 | 2.450e-4 | +2.106e-5 | +5.162e-4 | 31/50 |

Raw scale is therefore not a transferable error budget. Correlation changes
both the distribution of realized root error and how a solver reacts to its
direction.

### Same realized root error

Each draw was next rescaled to exactly `2.25e-4` joint-reach-weighted root L2.
This reverses any simple claim that correlation is intrinsically worse.

| Error grouping | Solver / anchor | Mean treatment Δ | Worst treatment Δ | Improving seeds |
|---|---|---:|---:|---:|
| Concrete IID | LCFR / 0.990 | -5.477e-5 | +8.799e-5 | 41/50 |
| Concrete IID | LCFR / 0.995 | -3.740e-5 | +4.288e-4 | 41/50 |
| Concrete IID | CFR+ / 0.990 | -5.587e-5 | +1.064e-4 | 43/50 |
| Concrete IID | CFR+ / 0.995 | -3.199e-5 | +4.347e-4 | 41/50 |
| Public-history | LCFR / 0.990 | -4.909e-5 | -4.719e-6 | 50/50 |
| Public-history | LCFR / 0.995 | -3.748e-5 | +3.234e-5 | 29/50 |
| Public-history | CFR+ / 0.990 | -3.537e-5 | -2.683e-5 | 50/50 |
| Public-history | CFR+ / 0.995 | -3.090e-5 | -4.804e-6 | 50/50 |

In this boundary there is only one public error group; after two-player
zero-sum normalization and fixed-magnitude calibration it has only two error
directions. The counts are consequently a mechanism check, not a population
estimate for neural range errors.

### Same on-policy root error, different location

For LCFR with anchor 0.99, 20 draws in every cell were fixed at the same
`2.25e-4` on-policy root L2. `Max CF root L2` is the larger of the two
player-specific counterfactual error contributions.

| Grouping | Error scope | Mean max CF root L2 | Mean treatment Δ | Worst treatment Δ | Improving seeds |
|---|---|---:|---:|---:|---:|
| Concrete IID | All leaves | 3.367e-4 | -6.270e-5 | +8.484e-5 | 17/20 |
| Concrete IID | High-reach half | 2.697e-4 | -8.381e-5 | +2.479e-6 | 19/20 |
| Concrete IID | Low-reach half | 1.786e-3 | +7.672e-5 | +1.261e-4 | 0/20 |
| Public-history | All leaves | 3.080e-4 | -5.062e-5 | -4.719e-6 | 20/20 |
| Public-history | High-reach half | 2.583e-4 | -7.273e-5 | -3.375e-5 | 20/20 |
| Public-history | Low-reach half | 8.373e-4 | +7.108e-5 | +1.236e-4 | 0/20 |

The low-reach half contains only 4.43% of on-policy frontier mass. Matching the
same on-policy root error there required about five times larger local error,
which created much larger counterfactual error and failed every run. A
reach-only scheduler could therefore starve precisely the leaves whose local
uncertainty it has allowed to become dangerous.

Systematic bias showed the same lack of a universal scalar threshold. With
LCFR/0.99 and error on every leaf, player-0 biases of `+/-3e-4` still improved
the blueprint, with smaller margins; biases of `+/-1e-3` reversed the gain.
The two signs caused different amounts of harm.

**Verdict:** promote root-scaled and per-player counterfactual error metrics;
reject raw perturbation scale, uniform RMSE, correlation, or joint reach as a
standalone scheduler signal. The future allocator needs local calibrated
uncertainty, counterfactual/opponent reach or action sensitivity, error
provenance, and minimum rare-branch coverage. No anchor/no-op rule is frozen
yet: solver, anchor, direction, and location still interact.

**Reproduction:** the tracked configs are
`leaf-kuhn2-depth2-structured-noise-matrix.json`,
`leaf-kuhn2-depth2-structured-bias-matrix.json`,
`leaf-kuhn2-depth2-correlation-focus-matrix.json`,
`leaf-kuhn2-depth2-correlation-calibrated-matrix.json`, and
`leaf-kuhn2-depth2-calibrated-structure-matrix.json` under
`experiments/configs/`. Raw result JSON remains locally generated and ignored.

## EXP-0008: Frozen counterfactual-risk selector v1

**Date:** 2026-08-19

**Status:** Rejected by preregistered holdout.

**Pre-registration:** commit `96d0489`; frozen rule SHA-256
`c6271e3a00d44ed9777d197914f86ff08e654ad7ead90db9ff3e345d4f96208d`.
No holdout outcome existed before that commit. The candidate was the LCFR/0.99
average after 100 iterations. It searched only when maximum player-specific
counterfactual root L2 was at most `2.0e-4`; otherwise it retained the
blueprint.

The rule had selected 312 of 773 deduplicated two-player development cases with
no observed failure. Its holdouts changed blueprint strength, depth, player
count, error targets, seeds, correlation, and location without retuning.

### Preregistered gate result

| Family | Cases | Searched | Harmful/tied searches | Mean selected Δ NashConv | Worst selected Δ | Unconditional-search mean Δ |
|---|---:|---:|---:|---:|---:|---:|
| Kuhn2 holdout | 1,440 | 788 | 434 | +3.03543e-5 | +3.66211e-3 | +9.02753e-5 |
| Kuhn3 holdout | 480 | 208 | 104 | +4.24468e-5 | +6.42303e-4 | +1.20990e-4 |

Positive delta is worse than the blueprint. V1 reduced the damage of
unconditional search, but permanent no-op has zero delta and beat both. Its
net improvement per reference search millisecond was negative in both
families. The two-player matrix took 87.3 seconds; the smaller three-player
matrix took 395.2 seconds, demonstrating the steep cost of exact multiplayer
auditing.

### Resolver regime dominates risk

| Game | Blueprint iterations | Depth | Selected | Harmful/tied | Mean selected Δ NashConv |
|---|---:|---:|---:|---:|---:|
| Kuhn2 | 50 | 1 | 141 | 141 | +6.51914e-5 |
| Kuhn2 | 50 | 2 | 122 | 0 | -4.25589e-4 |
| Kuhn2 | 300 | 1 | 140 | 140 | +2.66294e-4 |
| Kuhn2 | 300 | 2 | 122 | 0 | -2.42656e-4 |
| Kuhn2 | 3,000 | 1 | 141 | 141 | +5.28184e-4 |
| Kuhn2 | 3,000 | 2 | 122 | 12 | -9.29859e-6 |
| Kuhn3 | 300 | 2 | 53 | 0 | -5.67388e-5 |
| Kuhn3 | 300 | 3 | 51 | 0 | -1.19542e-4 |
| Kuhn3 | 1,500 | 2 | 53 | 53 | +2.71896e-4 |
| Kuhn3 | 1,500 | 3 | 51 | 51 | +7.41717e-5 |

At the near-exact error target `1e-8`, all 360 two-player cases searched and
180 were harmful; all 120 three-player cases searched and 60 were harmful.
Thus better leaves cannot repair the selector. Depth-one hybrid search was
intrinsically negative in this test, and the same anchored resolver changed
sign with three-player blueprint strength.

**Verdict:** reject risk-only authorization. Leaf uncertainty remains a useful
veto, but search also needs a conservative benefit/headroom estimate and an
explicit latency cost. The next mechanism test should evaluate blueprint local
counterfactual regret, a short probe solve, and predicted depth-limited gain as
benefit features against exact-control improvement. A v2 rule is not proposed
until one of those signals separates the held-out regimes without using
blueprint iteration count or full-game NashConv.

## EXP-0009: Resolver-benefit and progressive-probe signals

**Date:** 2026-08-19

**Status:** Observed mechanism failure; no v2 selector frozen.

This experiment removes leaf error entirely and asks a narrower question: can
information available inside the resolver predict whether deploying its
candidate will improve the untouched full game? Every depth-limited leaf is the
exact blueprint continuation value. Signal calculations use only that local
model; exact full-game NashConv is revealed afterward as the target.

The two-player grid contains 72 distinct candidates: six blueprint strengths,
two depths, three anchor weights, and LCFR/CFR+. The three-player grid contains
another 72: four blueprint strengths, three depths, three anchors, and the same
two solvers. Each candidate is observed after 1, 3, 5, 10, and 25 deterministic
probe iterations and after a full 100-iteration search, producing 360 raw runs
per game. Full search improved 32/72 two-player candidates and 26/72
three-player candidates.

`AUC` measures only ranking of positive versus nonpositive full-game outcomes;
0.5 is random. It is not a safety guarantee or a deployable threshold.

| Higher-is-better feature | Available | Kuhn2 AUC / rho | Kuhn3 AUC / rho | Combined AUC / rho |
|---|---|---:|---:|---:|
| Blueprint local CF regret | Before search | 0.631 / +0.378 | 0.565 / +0.021 | 0.600 / +0.193 |
| Probe model gain at 3 | After 3 iterations | 0.358 / -0.080 | 0.687 / +0.310 | 0.459 / -0.054 |
| Negative policy TV at 5 | After 5 iterations | 0.805 / +0.550 | 0.716 / +0.512 | 0.709 / +0.468 |
| Negative TV slope, 3 to 5 | After 5 iterations | 0.890 / +0.707 | 0.592 / +0.117 | 0.718 / +0.399 |
| Inverse-iteration gain estimate at 10 | After 10 iterations | 0.857 / +0.564 | 0.306 / -0.356 | 0.639 / +0.269 |
| Full local-model gain | After search | 0.891 / +0.652 | 0.509 / +0.002 | 0.718 / +0.389 |
| Full local gain / mean policy TV | After search | **0.968 / +0.747** | **0.686 / +0.364** | **0.855 / +0.633** |
| Negative full policy TV | After search | 0.823 / +0.576 | 0.686 / +0.494 | 0.721 / +0.486 |

The most tempting probe extrapolations do not transfer. The 10-iteration
asymptotic estimate changes from useful in Kuhn2 to anticorrelated in Kuhn3.
The direction of the raw three-iteration gain also reverses. A fitted pooled
classifier could hide this domain shift, so none was fit.

Post-search local gain per unit policy movement is the strongest observed
ranking feature. Policy displacement appears to proxy compositional risk: a
small modeled improvement bought with a large strategy change is suspect. But
raw sign still fails badly. Local-model gain was positive in 70/72 two-player
candidates, including 38 harmful candidates. It was positive in 63/72
three-player candidates, including 40 harmful candidates, and missed three
beneficial candidates. The ratio is therefore a candidate feature for later
calibration, not authorization.

The mechanism is now explicit. Exact continuation values make fixed-policy
expected utility identical in the local model and full game to numerical
precision. They do not make local and full best responses identical: a full
responder can deviate below the frontier, while the local evaluator cannot.
Consequently local NashConv improvement can coexist with full-game harm. This
is a resolver-composition problem, not a neural-leaf-error problem.

### Reference cost

| Probe checkpoint | Kuhn2 ms / full-search fraction | Kuhn3 ms / full-search fraction |
|---:|---:|---:|
| 1 | 0.337 / 1.2% | 2.785 / 1.0% |
| 3 | 0.923 / 3.3% | 8.222 / 3.1% |
| 5 | 1.515 / 5.2% | 13.645 / 5.1% |
| 10 | 2.983 / 10.4% | 27.302 / 10.1% |
| 25 | 7.257 / 25.0% | 67.820 / 25.1% |

Mean full-search time was 28.943 ms in Kuhn2 and 270.766 ms in Kuhn3 in the
reference Python runner. Blueprint signal evaluation added 1.125 ms and 10.217
ms respectively; post-search candidate-model evaluation added 1.992 ms and
17.223 ms. These timings characterize the reference workload, not a production
kernel.

**Verdict:** reject local headroom, a scalar probe endpoint, trajectory
extrapolation, or local gain sign as the missing benefit authorization term.
Retain policy movement and gain-per-movement as risk-aware ranking candidates.
Before neural scaling or a v2 preregistration, implement a complete small-game
continual resolver and measure whether it removes the frontier-deviation gap.

**Reproduction:** generate the two trajectory matrices with
`benefit-kuhn2-regimes-matrix.json` and
`benefit-kuhn3-trajectory-matrix.json`, then run
`python -m pontius.benefit_trajectory` as documented in `RUNBOOK.md`. Raw JSON
remains locally generated and ignored.

## EXP-0010: Public-belief continual composition

**Date:** 2026-08-19

**Status:** Rejected architecture; retained as a negative control.

EXP-0009 showed that a searched prefix could look better locally while harming
the full game. This experiment tests whether resolving every public decision
fixes that composition error. At each public history, the continual control:

1. reconstructs the joint posterior over private deals from the already
   composed ancestor policy;
2. solves a depth-limited game with exact blueprint continuation values;
3. deploys only the current public root's information sets; and
4. leaves zero-reach off-path histories on the blueprint.

Every information set is written at most once. Unit tests verify Bayes updates,
final-prefix posterior consistency, complete information-set coverage, a full-
anchor no-op, and off-path fallback. This is coherent Bayesian policy
composition, not safe resolving: it supplies no opponent counterfactual-value
guarantee at the replacement frontier.

Four target-blind architectures share the blueprint, solver, iterations,
anchor, and exact leaves:

- `Prefix` deploys every information set from one root depth-limited solve.
- `Continual` independently deploys one root strategy at every public history.
- `Local-gated` runs the same continual resolver but vetoes a root replacement
  unless exact local-model NashConv improves.
- `Global` is one coherent full-game anchored solve. It is an exact-game
  control, not a deployable hold'em architecture.

Positive improvement means lower full-game NashConv. Decision compute for
continual policies is reach-weighted expected search time per hand. The local
gate also includes its required exact local evaluation; optional diagnostics
are excluded. Reported quality/ms is the mean of per-case rates.

### Two-player matrix

The grid contains 72 paired cases: six blueprint strengths, depths one and two,
three anchors, and LCFR/CFR+.

| Architecture | Positive cases | Mean improvement | Worst improvement | Mean decision ms | Mean improvement/ms |
|---|---:|---:|---:|---:|---:|
| Prefix | 32/72 | -2.61671e-4 | -2.62138e-3 | 27.312 | -2.20200e-5 |
| Continual | 21/72 | -3.03646e-3 | -1.49190e-2 | 47.430 | -8.05744e-5 |
| Local-gated | 29/72 | -2.79147e-3 | -1.49190e-2 | 49.893 | -7.30929e-5 |
| Global | **68/72** | **+6.98319e-4** | -1.09587e-4 | 38.458 | **+1.81830e-5** |

Continual beat prefix in only 15/72 cases. The local gate improved on raw
continual in 22 cases, but global still beat it in 55/72. The four global
failures are duplicate depth rows for the strongest 3,000-iteration blueprint,
the loosest 0.97 anchor, and both solvers. Coherent search therefore still
needs a trust region; coherence is necessary, not sufficient.

### Three-player focus matrix

The grid contains 24 paired cases: 300- and 1,500-iteration blueprints, depths
one through three, anchors 0.99/0.995, and LCFR/CFR+.

| Architecture | Positive cases | Mean improvement | Worst improvement | Mean decision ms | Mean improvement/ms |
|---|---:|---:|---:|---:|---:|
| Prefix | 10/24 | -6.75439e-5 | -6.42303e-4 | 273.764 | -2.73813e-7 |
| Continual | 2/24 | -9.00442e-4 | -2.37479e-3 | 753.155 | -1.78676e-6 |
| Local-gated | 4/24 | -7.73361e-4 | -2.37442e-3 | 791.236 | -1.62187e-6 |
| Global | **24/24** | **+2.09830e-4** | **+3.09260e-5** | 636.080 | **+3.30268e-7** |

Global beat continual and local-gated continual in every case. Continual beat
prefix only twice. The gate searched all 12 public histories and deployed nine
on average, so it saved no search time; its required exact local evaluation
added 34.518 ms per expected hand. In Kuhn2 it deployed 3.49 of four histories
and added 2.301 ms.

Local rank statistics do not rescue deployment. In Kuhn3, reach-weighted root
model gain has AUC 0.909, yet its sign is positive in all 24 cases: two true
positives and 22 false positives. In Kuhn2 it makes 45 false-positive and 19
true-positive sign calls. A high AUC under severe class imbalance can coexist
with a useless zero threshold.

### Terminal-depth audit

A six-case Kuhn2 audit uses a 1,000-iteration blueprint and depth three, which
reaches true terminals from every public root. It varies LCFR/CFR+ and anchors
0.99, 0.995, and 0.999.

| Architecture | Positive cases | Mean improvement | Worst improvement |
|---|---:|---:|---:|
| Prefix / Global | 6/6 | +1.18143e-4 | +5.38385e-5 |
| Continual | 0/6 | -1.17723e-3 | -2.79728e-3 |
| Local-gated | 4/6 | -6.34707e-4 | -2.79728e-3 |

Prefix and global are identical here because the root solve spans the complete
game. Independent public-root replacement still fails. Thus the mechanism is
not leaf truncation, posterior drift, solver convergence, or missing public
states. A common Bayesian posterior preserves on-policy beliefs but not each
opponent's blueprint counterfactual values. Later strategy replacement opens
profitable deviations through earlier and off-path information sets.

**Verdict:** reject naïve Bayesian continual resolving and exact local no-op
gating. Stop tuning their CFR rule, depth, or anchor as the primary fix. Retain
them as falsification controls. The next resolver must first preserve opponent
counterfactual frontier values in two-player zero-sum Kuhn through a safe
resolving gadget. Only after that control passes should per-opponent constraints
or conservative relaxations be tested in multiplayer games.

**Reproduction:** use `composition-kuhn2-matrix.json`,
`composition-kuhn3-focus-matrix.json`, and
`composition-kuhn2-full-depth-audit.json` under `experiments/configs/` with
`python -m pontius.composition_matrix`. Raw JSON remains locally generated and
ignored.

## EXP-0011: Exact opponent-frontier safe resolving

**Date:** 2026-08-19

**Status:** Safety control verified; unconditional finite-residual deployment
rejected.

This checkpoint implements the two-player terminate/follow resolving game. At
each Kuhn2 public boundary, initial chance samples concrete private states in
proportion to chance reach times the resolver's trunk reach, excluding the
opponent's reach. The opponent receives one opt-out information set per private
card. Terminating returns its exact blueprint counterfactual-best-response
value; following enters a utility-scaled copy of the complete subgame. Only the
resolver player's subgame strategy is exported.

The exact candidate certificate has a useful identity: opponent gadget
best-response value above the opt-out baseline equals the sum of positive
candidate frontier violations. With the other full-game component fixed, half
that value bounds the increase in exploitability. Nested solves add their
one-sided bounds. Full-game evaluation is revealed only after construction.

The 32-case matrix crosses blueprint iterations 20, 100, 1,000, and 3,000;
LCFR/CFR+ search; and 30, 100, 300, and 1,000 iterations. `Strict` deploys a
boundary only when exact total positive frontier violation is at most `1e-12`.
`Global` is a from-scratch coherent full-game solve at the same iteration count.

| Architecture | Positive | Mean improvement | Worst improvement | Mean decision ms | Aggregate improvement/ms | Bound failures | Deployed roots |
|---|---:|---:|---:|---:|---:|---:|---:|
| Raw safe continual | 9/32 | -7.05082e-3 | -4.24750e-2 | 251.458 | -2.80398e-5 | 0/32 | 128/128 |
| Strict safe continual | 9/32 | +1.27000e-3 | 0 | 250.749 | +5.06482e-6 | 0/32 | 18/128 |
| Global control | 12/32 | +2.51098e-3 | -9.87721e-3 | 120.751 | +2.07946e-5 | n/a | n/a |

The independent single-boundary audit adds 128 candidate checks and has zero
bound failures; 31 candidates improve the full game. The raw composed arm also
has no bound failure—the problem is that its finite residual is large enough
to permit the observed harm. Its mean exploitability-increase allowance is
`5.48317e-3`. A correct bound can honestly certify that a weak solve may be
bad; it is not itself a no-harm guarantee.

### Convergence

| Search iterations | Raw positive / mean improvement | Strict positive / mean improvement | Global positive / mean improvement |
|---:|---:|---:|---:|
| 30 | 1/8 / -2.57224e-2 | 0/8 / 0 | 2/8 / -3.86808e-3 |
| 100 | 2/8 / -3.22312e-3 | 2/8 / +1.75208e-3 | 2/8 / +2.98289e-3 |
| 300 | 3/8 / -3.03925e-4 | 3/8 / +1.52807e-3 | 4/8 / +5.16284e-3 |
| 1,000 | 3/8 / +1.04617e-3 | 4/8 / +1.79984e-3 | 4/8 / +5.76627e-3 |

The strict arm helps mainly when the blueprint is weak: it improves 6/8 cases
at 20 blueprint iterations with mean `+5.04616e-3`. It improves 2/8 at 100,
none at 1,000, and one by only `2.06972e-6` at 3,000. This is consistent with
safe reconstruction having little headroom on a near-equilibrium blueprint.

Exact certificate evaluation averages about 5% of safe decision compute in
this tiny game; gadget traversal dominates. Even so, safe continual search
averages roughly twice the latency of the global control because each public
boundary adds an opt-out layer and is solved separately. Exact certification
will not remain cheap at poker scale.

**Verdict:** accept the gadget and additive residual certificate as the
two-player correctness oracle. Retain strict frontier gating as the permanent
non-harming control. Reject raw finite-iteration Resolve as deployment logic.
Safety alone does not maximize strategy quality per millisecond: next build an
exact constrained or max-margin oracle, then measure whether CFR convergence or
the feasibility-only objective is limiting useful safe improvement.

**Reproduction:** run
`safe-composition-kuhn2-convergence-matrix.json` under
`experiments/configs/` with `python -m pontius.safe_composition_matrix`. Raw
JSON remains locally generated and ignored.
