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
