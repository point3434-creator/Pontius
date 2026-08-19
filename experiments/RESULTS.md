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
