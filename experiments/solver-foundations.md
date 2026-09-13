# Solver updates, multiplayer controls, and leaf sensitivity

[Results index](RESULTS.md) · Updated 2026-09-12 · Historical controls and retained river research

**Conclusion:** these experiments established useful solver controls and exposed
why a locally converged search can worsen a strong blueprint. They did not
identify a universal update rule or a deployable multiplayer resolver. Update
rankings changed with game, iteration budget, anchoring, and leaf error. The
durable lesson is to evaluate the resulting policy in the original game, retain
an exact-leaf control, and measure where approximation error occurs.

The historical section covers EXP-0001–0007, recorded on August 18–19, 2026. Their favorable
anchoring results were exploratory controls; later held-out selection and
resolving results belong in [Safe search](safe-search.md). This consolidation
reads retained reports and configurations; it does not rerun the experiments.

**Reading the terms:** a *blueprint* is the frozen baseline policy; *no-op*
keeps it. *NashConv* sums each player's gain from a unilateral best response,
so smaller is better; it is not a win rate. *Average policy* accumulates
iteration policies, while *current policy* is the final iterate. *Counterfactual
reach* excludes the evaluated player's own action probabilities, retaining
chance and opponents' reach. *Δ NashConv* below means change from the blueprint
unless an exact-control comparison is explicitly named; negative is better.

## River representation and solver findings through 2026-09-12

The recent chain contains 39 retained milestones, from development-001 through
river-lp-presolve-001. The [complete experiment index](../docs/research/README.md)
links the individual reports, frozen designs, and raw evidence. These results extend
the older solver controls below; they do not replace their different populations.

**Current conclusion:** learned hand groups can preserve strategically useful information,
and exact acceptance checks can protect local repairs. However, direct full-hand LP solving
is now the better reference operating point on the four tested restricted river games.
The larger-tree follow-up below reaches a memory boundary in the deep-stack state.

| Question | Finding and retained evidence | What it supports, and what it does not |
|---|---|---|
| Does strategically informed grouping transfer? | The first [holdout](../docs/research/river-abstraction-holdout-001.md) reduced mean exploitability 15.39% versus uniform-equity bins, but only 2.17% versus range-equity groups; both comparisons won three cases and lost one. | The development gain of 49.19% shrank materially. Board and range dependence must remain visible. |
| Is remaining error caused by training or grouping? | [Certified grouping floors](../docs/research/river-group-optimality-001.md) separate representational restrictions from the policy's remaining gap across eight cases and 96 saved profiles. | More iterations cannot remove a certified fixed-group floor. This is a useful diagnostic independent of which grouping wins. |
| Can a learned target preserve useful decisions? | Frozen ordinary action-preference models [confirmed](../docs/research/river-witness-preference-confirmation-001.md) a 23.32% lower mean grouping floor versus range-response on 16 new boards / 96 cases; 15 board means improved and one worsened. | Directional and declared sensitivity criteria passed. These are restricted-game comparisons, not a neural-versus-tabular bot-strength result or a statistical confidence level. |
| Did more elaborate features consistently help? | [Clipped targets](../docs/research/river-witness-clipped-target-001.md) repaired severe cases while worsening most others. [Ordinal targets](../docs/research/river-witness-ordinal-001.md) failed the practical replacement criteria. [Soft assignment](../docs/research/river-witness-soft-assignment-001.md) failed both primary support criteria. | Preserve these non-improvements. Better fit or richer features alone do not establish a better resulting strategy. |
| Can a local regrouping repair beat continued training? | The [size-aware repair confirmation](../docs/research/river-multibet-size-confirmation-001.md) accepted 13 of 16 candidates, rejected three, and lowered mean error 8.83% versus continuation at about 13% more compute. | A fixed-capacity bettor split/merge with a fixed caller and an exact security gate earned a [frozen research baseline](../docs/research/river-multibet-size-repair-baseline.md). It is not a general multiplayer safety theorem. |
| Do alternative update recipes improve this learner? | [Regret variants](../docs/research/river-regret-variants-001.md) compared plain regret matching, regret matching plus, and discounting on the same 16 cases. At 50,000 updates, plain matching had the lowest mean residual and error; targets passed 16/16, 12/16, and 14/16 respectively. | The two alternatives did not earn fresh confirmation. These are fixed-game best-response learner adaptations, not a universal ranking of CFR algorithms. |
| Does repair survive reached ranges? | [Public-range transfer](../docs/research/river-blueprint-range-transfer-001.md) used four reached river states and all 1,081 holdings per role. Repair beat continuation in all four normalized games, with a 19.43% mean reduction; one case contributed about 89.74% of total gain. | A useful pilot, heavily concentrated and based on an early fallback-heavy blueprint. Changing range source and hand-pool size together prevents a clean causal attribution. |
| Does the actual stack preserve the repair opportunity? | [Actual-stack transfer](../docs/research/river-stack-transfer-001.md) found that half-pot and pot-sized bets both collapse to all-in in three of four states. The sole distinct-size case improved about 2.10%. | Three cases are structurally inapplicable to size repair, not failed repairs or excluded inconvenient outcomes. Do not pool only the eligible case into a full-population claim. |
| Is compression necessary in these river games? | [Direct full-hand comparison](../docs/research/river-full-combo-direct-002.md) gave lower measured error and shorter measured solve time in all four cases than the existing 50,000-update K=16 learner. | This compares particular LP and iterative implementations, changing solver and representation together. It does not establish an inherent speed advantage of full representation. |

### Presolve capacity non-improvement: river-lp-presolve-001

The [six-worker comparison](../docs/research/river-lp-presolve-001.md) varied only
presolve on/off on the same three deep-stack trees. Both expanded trees hit memory
stops under both settings. The two baseline arms passed separate exact verification;
turning presolve off reduced peak memory from 2082 to 1904 MiB but increased compute
from 6.34 to 7.95 seconds in this single pair. Entered paired LP matrices were identical.

Disabling presolve alone is insufficient. Censored stop times and peaks do not rank
completed solves. Close the toggle here; next compare a full-hand iterative method
using direct payoff products with the LP reference, measuring memory and original-game
exploitability against compute. Keep private-hand detail, menus and strict acceptance
claims fixed. No iterative implementation or capacity improvement is established yet.

### Native memory boundary: river-lp-memory-001

The [same-cell memory diagnostic](../docs/research/river-lp-memory-001.md) places both
deep-stack stops inside the first native HiGHS run(), after model loading. Checkback
entered at 929 MiB and peaked at 3334 MiB; raise entered at 1698 MiB and peaked at
6237 MiB. Both controls reproduced the exact prior baseline policy and certificate.
Copies are measurable, but the larger memory increase occurs inside native solving.
The trace cannot yet distinguish presolve from later simplex or factorization work.

The original path filter missed SciPy frames under isolated Windows imports. That
incomplete attempt is preserved; a normalized filter, failing-original/passing-corrected
boundary control and separately frozen rerun supply the actual phase diagnosis.
The subsequent presolve comparison above follows this proposal and finds no capacity
recovery. The remaining native allocation is not isolated by these measurements.

### Larger action tree: river-tree-expansion-001

The [nested-tree test](../docs/research/river-tree-expansion-001.md) now covers betting
after a check and one all-in raise response. Seven of nine distinct full-range cells
have independently verified strict certificates. The three shallow-stack expanded
trees needed 8.18-10.05 seconds compute, versus 2.87-3.13 seconds for their controls.
Both expanded deep-stack cells hit the sampled memory stop; no policy score is imputed.
Three raise variants are identical all-in aliases, not additional replications.

An all-zero payoff edge case initially broke separate verification. A one-line correction
in a copied verifier and additional nonzero exhaustive-response controls verified the
seven saved strategies without rerunning any solver. Original failed receipts remain.
The subsequent memory diagnostic above locates the dominant increase inside native
solving, leaving its internal stage as the next controlled question.

### Numerical closure: lp-numerical-scaling-001

The [fixed scaling diagnostic](../docs/research/river-lp-numerical-scaling-001.md)
closed both earlier strict misses: all four corrected full-hand strategies pass the
unchanged original-matrix threshold, with errors from 4.30e-16 to 2.99e-15 normalized
chips and solve/certificate times of 1.49-4.58 seconds. HiGHS had dropped small
probability-weighted coefficients; exact power-of-two value rescaling kept them above
its cutoff. All original results remain preserved, and no production solver changed.
Four preflight tests, separate original-matrix verification, and coefficient/vector
round-trip checks passed. The subsequent larger-tree result above supplies that next capacity test.

### Pre-correction full-hand detail and numerical boundary

Each case represents all 1,081 holdings per player and 1,070,190 collision-free ordered
deals. Check ends at showdown; a bet permits only fold or call. Three cases have one
all-in size; one has sizes 14 and 29. There are no subsequent bets or raises.

| Situation | K=16 error | Full-hand error | Strict full-hand threshold | Grouped time s | Full time s |
|---|---:|---:|---|---:|---:|
| 1 | 0.005186013919 | 4.9555902445e-9 | Pass | 5.412 | 1.373 |
| 2 | 0.015486020143 | 1.3708768849e-7 | Miss | 7.596 | 4.604 |
| 3 | 0.001701045209 | 4.4643936436e-9 | Pass | 5.572 | 1.481 |
| 4 | 0.003740553750 | 2.1649312889e-8 | Miss | 5.601 | 1.387 |

Error is half the unrestricted-response gap, with payoffs normalized by 10/actual pot.
Strict acceptance requires gap <= 1e-8, hence error <= 5e-9. All four LP pairs returned
numerical success; only two passed that exact threshold. The other errors were recovered
from retained vectors without another solve or a relaxed threshold. See the
[post-run assessment and four per-hand CSVs](../experiments/river-abstraction-study/full-combo-direct-002/assessment.md).
Exact rational bounds concern the stored binary64 payoff matrix.

Times include each arm's solve and final scoring/certification, exclude shared preparation
(0.372-0.536 s) and grouping-floor diagnostics, and have one observation per case.
Whole-worker OS peak commit was 1,106-2,220 MiB, including both arms and diagnostic LPs;
it cannot be assigned exclusively to either solver. The first attempt observed the
Windows launcher rather than its worker, invalidating its memory figures and stop claims.
Its bytes remain under superseded-attempt/. The corrected run checked the executing PID
and observed a 128 MiB allocation. Its 50 ms sampled memory stop is not a hard cap.

### What to retain, pause, and test next

- Retain certified grouping floors, full-hand best-response scoring, per-role acceptance
  gates, and matched continuation controls as reusable research tools.
- Keep the successful learned grouping and size repair as frozen comparison baselines.
  Pause incremental target/repair tuning on this restricted family.
- The fixed numerical scaling now supplies four certified references for these games.
  Preserve the original two misses and their raw vectors as the diagnostic predecessor.
- The native-memory diagnostic and presolve comparison did not recover the deep-stack
  trees. Next compare full-hand iterative payoff-product solving against the LP
  references on the same games, measuring quality, complete cost and memory.

All 39 milestones remain separate records, including failures and corrections. They
are not 39 independent replications: many diagnostics reuse observed panels. Finite-game
enumeration removes match-sampling variance within each declared game; it does not remove
uncertainty from board selection, range modeling, or transfer to another betting tree.
Reached ranges are factorized and fallback-heavy; folded-player cards are not jointly
marginalized. No result here establishes six-max playing strength or a live-clock resolver.
Python 3.14.6 was used for this research chain. No retained research was rerun for this
consolidation, and publication does not authorize another invocation or policy adoption.

## Time-budget quality: river-time-quality-001

The [time-budget quality campaign](../docs/research/river-time-quality-001.md)
completed six trajectories and 24 exact audits. All tested iteration increases
reduced error; repeat policies were identical. Under the declared accounting,
10 seconds fits 19.06x lower checkback error, and 15 seconds fits 9.58x lower
raise-tree error, relative to 2,048 iterations. Tight-budget misses remain
visible; no strict equilibrium threshold passed. Fresh-board transfer is next.

## Graph replay: river-gpu-graph-001

The [graph replay test](../docs/research/river-gpu-graph-001.md) completed
36 solves across 18 fresh workers and six independent rational audits.
Replay accelerated the fixed solve 8.48x / 6.09x versus eager GPU execution,
with bitwise-identical final policies across all arms, repeats and resets.
Preparation and audit costs reduce the gain but do not erase it.
The subsequent time-budget campaign above measures that quality improvement.

## GPU execution: river-gpu-execution-001

The [GPU execution assessment](../docs/research/river-gpu-execution-001.md)
measured 1.31x / 1.56x faster fixed-work solves on the two expanded trees,
with essentially unchanged independently audited error. Including fresh
solve processes and separate exact audits reduces the gain to 1.11x / 1.31x.
This was an exploratory continuation after a retained trajectory-parity
refusal, not an original-plan pass. Host GPU-process memory also increased.

The subsequent graph replay result is recorded above, with setup and audit charged.

## Expanded-tree capacity: river-cfr-expanded-001

The [expanded-tree comparison](../docs/research/river-cfr-expanded-001.md)
completed 24 training runs and eight independent rational audits within the
original sampled 3,072 MiB budget on both trees where LP stopped on memory.
This establishes checked approximate-solution capacity; it does not establish
strict equilibrium convergence or a live resolver. The report retains all
four fixed configurations, their quality curves, and full cost boundaries.

The subsequent GPU execution assessment is recorded above. Neural approximation remains
deferred; this experiment required no new private-hand compression.

## CFR confirmation: river-cfr-comparison-002

The [second position](../docs/research/river-cfr-comparison-002.md) adds milestone 41.
Unchanged solver and six parameter sets: paper DCFR+ has 6.56x less error than
matched CFR+; released-code DCFR+ again leads. Matched prediction improves
error about 11%, versus a 5.99x increase on the first case. Its effect is mixed.
All 18 repeats and six independent final rational audits completed. No strict
LP-threshold pass. This shorter-stack case has one distinct opening bet and
cannot establish capacity on the expanded trees. That test is now next.

## New CFR comparison: river-cfr-comparison-001

The [six-arm result](../docs/research/river-cfr-comparison-001.md) adds the 40th
milestone. On one retained full-range baseline river, paper DCFR+ reduced final
error 8.10x versus CFR+ with averaging held fixed. Matched prediction increased
error 5.99x relative to DCFR+. Released-code DCFR+ was best, but its denominator
differs from the paper and is separately labeled. Three repeats per arm matched
policy bytes exactly; six rational audits confirm residuals, not strict convergence.
Training took about 3.4 s per arm with roughly 129-131 MiB worker peak commit;
independent audits needed about 337 MiB. Confirm another case and expanded-tree
capacity before selecting a solver. The 39-milestone synthesis above remains
the historical boundary; this addendum supplies the newly measured evidence.

## Which results support those conclusions?

| Question | Measured result | Sample, scope, and limitation |
|---|---|---|
| Does linear weighting improve the initial control? | LCFR versus CFR reduced average-policy NashConv from **1.4427e-4 to 8.5944e-6** in two-player Kuhn and **7.7954e-4 to 1.229e-5** in three-player Kuhn. [EXP-0001](../docs/archive/experiment-results-through-2026-09-08.md#exp-0001-cfr-versus-lcfr-on-two-player-kuhn), [EXP-0002](../docs/archive/experiment-results-through-2026-09-08.md#exp-0002-cfr-versus-lcfr-on-three-player-kuhn) | One sequential run per arm; 20,000 and 5,000 alternating full-tree iterations respectively. These exact toy-game observations do not establish general multiplayer convergence. |
| Is one update rule consistently strongest? | At 20,000 two-player iterations, LCFR and CFR+ finished near **8.6e-6** NashConv. In three-player Kuhn, CFR+ led at 500 and 1,000 iterations; DCFR finished lowest at 5,000, **2.55287e-7**. [EXP-0004](../docs/archive/experiment-results-through-2026-09-08.md#exp-0004-four-cfr-update-rules) | Four rules, cold starts, exact leaves, fixed traversal. Solver times exclude exact evaluation; single runs do not establish speed differences or performance under sampling. |
| Can exact evaluation remain inside every training report? | Uniform-profile evaluation rose from **0.001 s** at two players to **106.623 s** at six. [EXP-0003](../docs/archive/experiment-results-through-2026-09-08.md#exp-0003-exact-evaluator-scaling-on-uniform-kuhn-profiles) | One evaluation per player count, two through six, including all players' exact best responses. This is a reference-hardware boundary in Kuhn, not a hold'em cost model. |
| Can shallow search harm the blueprint before adding leaf error? | Unanchored depth-one replacement increased NashConv by roughly **0.087**, against blueprint NashConv **1.87060e-4**, even with exact continuation values. Tiny perturbations then caused mean policy TV around **0.13**. [EXP-0005](../docs/archive/experiment-results-through-2026-09-08.md#exp-0005-paired-shallow-leaf-sensitivity) | Two-player Kuhn, 100 search iterations; perturbation measurements use five fixed seeds. Continuations were precomputed, and concrete-history noise does not validate neural leaves. |
| Can anchoring make deeper search useful? | Depth-two LCFR at anchor 0.99 improved the strong blueprint by **1.69448e-4** with exact leaves. CFR+ at anchor 0.995 improved **10/10** seeds at leaf RMSE **1.38657e-4**, but only **2/10** at **1.38657e-3**. [EXP-0006](../docs/archive/experiment-results-through-2026-09-08.md#exp-0006-blueprint-anchored-depth-two-search) | Six continuation leaves, 100 iterations, solver/anchor choices explored on the same game. Every selected solver's current policy worsened the strong blueprint despite its average improving. |
| Does the same on-policy error imply the same strategic risk? | At root L2 **2.25e-4**, low-reach-localized errors improved **0/20** draws for both tested groupings; high-reach errors improved **19/20** IID and **20/20** public-history draws. [EXP-0007](../docs/archive/experiment-results-through-2026-09-08.md#exp-0007-structured-and-reach-weighted-leaf-error) | LCFR/0.99, depth two. The low-reach half held only **4.43%** of frontier mass; matching root error required larger local errors and increased counterfactual error. This falsifies a reach-only shortcut, not all reach-based allocation. |

## What do these comparisons actually test?

The generalized multiplayer game uses N+1 ordered cards, one ante each, and
one possible one-chip bet with cyclic calls or folds and no raises. Different
multiplayer Kuhn conventions need separate comparisons.
[Rule definition](../docs/archive/ADR-0005-multiplayer-kuhn-rules.md)

CFR+ here uses regret flooring with **quadratic averaging**, and DCFR uses
parameters **(1.5, 0, 2)**. LCFR is the linear-weighting variant. Regret changes
are aggregated by information set before the update; changing that detail can
change the algorithm. [Update definitions](../docs/archive/ADR-0006-cfr-update-definitions.md)

The two-player evaluator matched exhaustive pure-policy enumeration for uniform
and passive profiles. The three-player response passed single-information-set
deviation checks, but an independent sequence-form cross-check remained open
in this evidence. Different multiplayer utility profiles cannot by themselves
rank quality, and finite low NashConv observations do not prove convergence.

## Which attractive shortcuts failed or needed correction?

- **Credit leaf accuracy for resolver quality.** The paired protocol separates
  treatment minus exact control from exact control minus blueprint. Exact
  blueprint continuations did not rescue the depth-one replacement.
  [Protocol](../docs/archive/ADR-0007-paired-leaf-error-protocol.md)
- **Use equal pseudo-regret mass as a neutral warm start.** CFR retained that
  prior more strongly than discounting variants. Its favorable warm-start
  comparison does not establish general superiority.
- **Blend only after searching.** For the strong blueprint, every tested nonzero
  output-only blend worsened NashConv. Constraining behavior during traversal
  produced useful averages, but partial anchoring supplied no safety guarantee.
  [Anchoring analysis](../docs/archive/ADR-0008-blueprint-anchored-search.md)
- **Treat correlation or RMSE as a universal risk score.** Public-history noise
  looked worse at equal raw scale, but that ordering changed after matching
  realized root error. There was only one public error group; calibration left
  just two error directions, so 50 successful seeds were not 50 diverse
  real-world error patterns. [Error analysis](../docs/archive/ADR-0009-reach-weighted-structured-leaf-errors.md)

## What remains unresolved, and where is the evidence?

Transfer to sampled, changing, multiplayer public-belief searches requires
separate evidence. So do a usable uncertainty estimator, a frozen choice among
search and no-op, and performance that includes leaf preparation. Depth two
helped this prefix-policy experiment; it does not imply that spending more on
depth generally improves play. Follow [Safe search](safe-search.md) for later
tests of these questions and [Exact evaluation](exact-evaluation.md) for the
cost of stronger evidence.

The early ledger records no experiment invocation SHA. Verified repository
commit **`91f031e91c957a9b273c2ccc345421f7b286b416`** contains its source ledger
at `experiments/RESULTS.md` and ADRs at their former `docs/decisions/` paths;
it is a recovery reference, **not** an asserted run commit. Retained local
details are in the [archived ledger](../docs/archive/experiment-results-through-2026-09-08.md).
Configurations include [two-player LCFR](configs/kuhn2-lcfr-20000.json),
[initial leaf matrix](configs/leaf-kuhn2-initial-matrix.json),
[anchored solvers](configs/leaf-kuhn2-depth2-anchored-solvers-matrix.json), and
[calibrated error locations](configs/leaf-kuhn2-depth2-calibrated-structure-matrix.json).
EXP-0007 explicitly says raw JSON was locally generated and ignored; no raw run
artifact is linked here as independently retained or revalidated.
