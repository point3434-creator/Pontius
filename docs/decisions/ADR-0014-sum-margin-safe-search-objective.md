# ADR-0014: Sum-margin is the first safe search objective

**Status:** Accepted provisionally 2026-08-19.

## Decision

Reject pure max-min frontier margin as the primary safe-search objective. It
is a useful feasibility and robustness diagnostic, but one immovable frontier
component can pin its value to zero and leave strategically different safe
policies tied.

Advance a target-free constrained sum-margin objective for the next solver
comparison. For every opponent augmented frontier information set, introduce a
nonnegative guaranteed margin constrained by every pure opponent continuation;
maximize the sum of those margins. This preserves every blueprint
counterfactual-best-response frontier value while preferring useful movement
inside the safe set.

Retain an exact LP that maximizes the current full-game opponent best-response
reduction under the same frontier constraints as a hidden diagnostic control.
It may label objective regret in exact games, but it is not deployable because
the full-game target and complete pure-response enumeration are unavailable at
poker scale. Its root-forward composition is greedy, not a proof of the
globally best continual policy.

## Construction

The exact oracle enumerates perfect-recall pure plans in the counterfactual
subgame and converts a mixed normal-form solution to an independently checked
behavioral strategy. A dependency-free two-phase simplex solves general
nonnegative LPs; a separate shifted packing solver cross-checks the max-min
matrix game.

For frontier entry `I`, opponent continuation `q`, and resolver plan `j`, let
`M[I,q,j]` be blueprint CBR value minus candidate counterfactual value. The
target-free program uses resolver mixture `x` and nonnegative margins `m_I`:

```text
maximize  sum_I m_I
subject to m_I <= sum_j M[I,q,j] x_j  for every I,q
           sum_j x_j = 1
           x_j, m_I >= 0
```

The hidden control instead maximizes nonnegative full-game opponent-BR
reduction while retaining `sum_j M[I,q,j] x_j >= 0` for every frontier response.
Every LP result is checked against dynamic counterfactual and full-game best
responses after mixed-to-behavioral conversion.

## Evidence

EXP-0012 crosses LCFR and CFR+ blueprints at 20, 100, 1,000, and 3,000
iterations. There are eight paired profiles, 32 public-boundary solves per
architecture, and no residual-adjusted bound failures.

| Objective | Positive | Mean NashConv improvement | Median | Mean decision ms | Aggregate improvement/ms |
|---|---:|---:|---:|---:|---:|
| Max-min frontier margin | 8/8 | `8.30711e-5` | `4.94315e-7` | 153.115 | `5.42540e-7` |
| Sum frontier margin | 8/8 | `3.56692e-3` | `7.97976e-4` | 150.904 | `2.36369e-5` |
| Hidden BR greedy control | 8/8 | `3.67755e-3` | `8.14478e-4` | 1662.488 | `2.21208e-6` |

Sum-margin beats max-min in all eight cases. It captures 96.9916% of hidden
improvement in aggregate, 98.9680% as the mean per-case fraction, and 94.9296%
in the worst case. Max-min is frequently pinned near zero even when a large
safe improvement exists. The target-free objective therefore removes nearly
all observed objective regret without paying for the hidden full-game target.

The decision times describe a standard-library Python normal-form oracle, not
a production kernel. The useful result is the paired objective comparison.

## Opposing evidence

- This is two-player Kuhn. Normal-form enumeration is exponential and cannot
  be transferred to six-player hold'em.
- Raw summed counterfactual margins may over-weight games with many frontier
  information sets or inconsistent payoff scales. Reach normalization,
  opponent grouping, and learned or dual-derived weights remain open.
- The hidden composed control is greedy across public boundaries. Its value is
  an exact conditional target at each boundary, not a global safe-policy
  optimum.
- An objective with a good exact optimum is not yet an efficient algorithm.
  CFR on the terminate/follow gadget was designed primarily for reconstruction
  and feasibility; it may approach this face of the safe polytope slowly.
- Safety still depends on exact frontier values. Approximate neural values
  require conservative uncertainty bounds before any deployment claim.

## Consequences

The next checkpoint compares finite CFR-family candidates with both exact
frontier-sum regret and hidden best-response regret at matched public
boundaries. It should test objective-aware tie-breaking or regularization before
spending large sweeps on LCFR versus CFR+ convergence alone.

The exact oracle becomes a teacher and falsification control. It does not enter
the planned runtime. Multiplayer extensions must state whose counterfactual
values are constrained, how conflicting opponents are weighted, and what
fallback applies when the feasible improvement set is empty.

## Cheapest falsifying experiment

At every EXP-0011 boundary and iteration checkpoint, measure the safe CFR
candidate's gap to the exact sum-margin optimum and its hidden conditional BR
optimum. If frontier-sum regret is already negligible while full-game regret
remains large, reject summed margin as the missing decision-relevance term. If
both gaps remain large, search convergence or objective implementation is the
immediate bottleneck.

## Kill criterion

Do not advance sum-margin beyond an exact-game teacher if it captures less than
80% of the hidden safe improvement on a held-out larger game or if any claimed
safe solution violates an exact frontier or nested exploitability bound by more
than `1e-10`.
