# ADR-0020: Measure opportunity before fitting a scheduler

**Status:** Accepted 2026-08-19.

## Decision

Accept the causal opportunity-trace schema and perfect-information allocation
controls as the next exact-lab measurement layer. Advance computation
allocation at the 5 ms regime, where a substantial within-blueprint opportunity
ceiling exists.

Do not fit or freeze a scheduler from the current features. The first two
candidate checkpoints improve no boundary even though 37/40 boundaries improve
later, and early scalar features rank future gain per millisecond weakly. A
myopic next-phase label would teach the wrong policy; a small model fit to these
40 revealed boundaries would mostly learn benchmark regime identity or timing
noise.

The next feature experiment is a cached, boundary-local blueprint residual and
stability probe. It must remain target-free, report its own compute cost, and
predict a multi-phase option value rather than only the next candidate's gain.

## Measurement contract

The dataset contains three explicit decision phases:

1. `boundary_start`: return the blueprint or buy an initial probe;
2. `candidate_ready`: return the certified incumbent or buy pricing plus a
   later candidate cycle; and
3. `after_pricing`: suspend the priced option or pay to consume it.

Candidate-ready features are assembled from an allowlist and cannot see the
current pricing score, reduced cost, column, or pricing time. Exact sum-margin,
hidden complete-game best-response values, and all future outcomes appear only
as labels. Tests mutate those oracle fields and verify that every online
feature remains unchanged. A second test mutates a current pricing result and
verifies that the same update's candidate-ready features do not change while
its post-pricing features do.

Cheap concentration summaries of the restricted-master mixture and response
duals are now recorded. They add observation only and do not alter the strategy
sequence.

## Observed development evidence

The two already revealed phase-v2 development matrices contain 40 boundaries
across ten fixed blueprint solver/strength regimes. They produce 40 start, 186
candidate-ready, and 186 post-pricing decisions. No scheduler is fit.

Opportunity is highly uneven. Across the mixed development set, the top 25% of
boundaries contain 87.19% of exact sum-margin headroom. That figure is inflated
by differences between blueprint strengths, so it is not the deployment
claim. Restricting concentration to each four-boundary fixed-blueprint regime,
then weighting by headroom, the largest one boundary contains 41.04% and the
largest two contain 70.20%.

At an average 5 ms pool within each fixed blueprint:

| Allocation control | Aggregate sum-margin capture |
|---|---:|
| Independent perfect phase fit under each hard 5 ms deadline | 47.7146% |
| Best perfect-information fixed checkpoint per blueprint regime | 67.635% |
| Perfect-information state-adaptive pool within each regime | 83.2072% |

The adaptive ceiling gains 15.57 percentage points over an already optimistic
per-regime fixed-checkpoint control. A looser cross-regime pool reaches 99.919%
but is explicitly excluded from the deployment claim because it moves compute
between different agents. Frozen update six captures 92.3114%, but uses 5.551
mean ms, 12.843 p95 ms, and overruns 5 ms on 15/40 boundaries.

A serial timing replicate preserves the 5 ms independent and regime-pooled
scores exactly; per-regime fixed capture changes only from 67.635% to 67.323%.
At 20 ms one boundary crosses a timing threshold, moving independent capture
from 99.887% to 97.498%. Kuhn2 saturates completely by the 20-50 ms pooled
budgets, so it cannot measure scheduler upside there.

## Multi-phase option evidence

Immediate reward is a misleading computation target:

- At `boundary_start`, 37/40 traces later improve, but the first candidate
  improves 0/40. The first gain requires 3.51 candidate checkpoints and 4.29
  ms on average, with a maximum horizon of six checkpoints.
- After candidate one, the next candidate still improves 0/40. A future gain
  remains in 37/40 traces and requires another 2.51 candidates and 2.78 ms on
  average.
- After candidate two, the next-candidate signal recovers only 24/37 future
  opportunities.

Therefore the scheduler action must be a preemptible macro-option such as
`price -> consume -> re-separate`, not an isolated phase whose immediate
incumbent delta is often zero.

## Why fitting does not advance yet

Unfitted Spearman diagnostics against best future gain per millisecond are
weak. The largest absolute correlation is about 0.15 at boundary start, 0.11
after the first candidate, and 0.11 after its pricing. Initial reduced cost is
mostly public-tree geometry: it correlates only about 0.11 with future gain per
millisecond. Across all phases, the strongest scalar restricted-master signals
reach only about 0.20.

The ceiling establishes that allocation can matter, not that the present
features can realize it. Fitting now would conflate ten blueprint regimes,
four public states per regime, and single-run wall timing.

## Dissent protocol

**Verdict:** advance opportunity-aware scheduling research at 5 ms; reject an
immediate scheduler fit.

**Confidence:** high that the causal accounting and exact Kuhn2 ceiling are
correct; moderate that a better target-free residual can recover useful
allocation; low that the measured magnitude transfers to six-player hold'em.

**Supporting evidence:** exact labels, monotone safe incumbents, causal
mutation tests, conservative/optimistic quantized allocation bounds, fixed-
blueprint pool scoping, and one serial timing replicate.

**Opposing evidence:** only four public boundaries exist per Kuhn blueprint;
the pool assumes saved work can be spent on another useful or speculative
state; Python phase time is noisy; exact safety separation is not scalable;
and sum-margin is not six-player poker EV.

**Largest unknown:** whether a cheap boundary-local blueprint residual or
uncertainty signal can rank multi-phase option value across unseen blueprint
regimes.

**Cheapest falsifying experiment:** compute a cached one-step counterfactual-
regret/stability summary per boundary, measure its standalone cost and
leave-one-regime-out rank quality, then compare a conservative macro-phase rule
with the best fixed checkpoint at 5 ms.

**Kill criterion:** if causal target-free features cannot beat the fixed
checkpoint on a fresh exact-game holdout after one residual/stability feature
experiment, keep fixed scheduling and defer learned value-of-computation until
the reduced hold'em environment provides richer workloads.

**Recommendation:** build the residual/stability measurement next. Preserve
the blueprint fallback and safe incumbent; do not start neural scheduling,
kernel specialization, or multiplayer safety relaxation from this result.
