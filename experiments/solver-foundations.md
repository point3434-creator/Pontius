# Solver updates, multiplayer controls, and leaf sensitivity

[Results index](RESULTS.md) · Consolidated 2026-09-08 · Historical exact-game evidence

**Conclusion:** these experiments established useful solver controls and exposed
why a locally converged search can worsen a strong blueprint. They did not
identify a universal update rule or a deployable multiplayer resolver. Update
rankings changed with game, iteration budget, anchoring, and leaf error. The
durable lesson is to evaluate the resulting policy in the original game, retain
an exact-leaf control, and measure where approximation error occurs.

This page covers EXP-0001–0007, recorded on August 18–19, 2026. Their favorable
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
