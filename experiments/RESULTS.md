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

