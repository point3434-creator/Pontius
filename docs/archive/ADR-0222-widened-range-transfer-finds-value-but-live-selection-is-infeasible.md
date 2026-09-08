# ADR-0222: Widened range transfer finds value, but live selection is infeasible

- Status: accepted fresh research result; current live path rejected
- Date: 2026-08-21
- Implements: ADR-0221
- Clean preregistration commit: `9df49d2`
- Result: `experiments/results/h32-action-conditioned-widened-selector-v1.json`
- Result SHA-256: `4f3b5af6133410e646452243883ce4c11934612e987122eafba2def327c218c7`

## Formal result

The one authorized fresh invocation passes every provenance, source, target,
warm-start, block-partition, feature-barrier, exact-teacher, memory, wall-time,
immutable-emission, and numerical gate. It completed in `2,244.506 s` from
clean commit `9df49d2`.

Every warm step changed exactly 192 coherent public nodes, producing 2,304
regret-vertex directions across the 12 frozen posteriors. All feature matrices,
structural schedules, affine envelopes, and capacities existed while all 2,304
labels were null. The later teacher phase made 1,863 independent exact
certificate queries; all 1,863 completed and had positive value. The remaining
441 directions had no affine-envelope scale and were assigned the frozen zero
realized B-to-C label.

ADR-0179 identity is strong. Maximum affine-intercept and Tier-A identity
errors are both zero. The affine envelope's predicted value at its selected
scale agrees with every exact teacher label to `6.11e-15`. GPU-pool allocation
peaks at `8,577,609,216` bytes and physical-free memory never falls below
`6,525,288,448` bytes.

## The widened library contains value

The pooled maximum realized B-to-C value is `0.1769733001`. Every target has a
positive oracle row. The full-library oracle exceeds the old common-six oracle
by roughly `330x` to `33.6 million x` per target. The six-block development
slice therefore omitted nearly all value in this action-conditioned
range-transfer regime.

This is not a deployed opportunity-magnitude claim. The target belief is
conditioned on an observed checks-then-bet prefix, but the h32 game is still
rooted at the beginning of the complete river tree. It consequently labels
edits at the observed action, before it, and on counterfactual branches that a
post-action bot can no longer choose. The enormous lift is evidence that the
complete-tree range-transfer corpus is direction-rich; it is also evidence
that continuation rooting is now necessary before interpreting the magnitude
as live opportunity.

## The retained composite transfers only partially

The frozen Tier-B objective-slope times cap-radius composite has within-target
Spearman correlations from `0.8131` to `0.9972` and selects the exact best row
on 6 of 12 targets. It captures `62.7233%` of pooled full-library value.

The miss mechanism is identified. Fresh cap radii are commonly one while
selector-stable radii vary sharply. The old composite omits that selector
window. Its top row has selector-stable radius zero and no envelope scale in
the two zero-capture targets. Both stop `objective_nonimproving`. Other partial
misses similarly favor a large slope whose safe selector window is too short
to accumulate the most value. This confirms the preregistered prediction that
misses concentrate at window-boundary effects.

The complete affine envelope ranks all 12 realized-label winners and matches
their exact labels, but this is a validation of the B-to-C affine certificate,
not an independent selector discovery: the frozen label is explicitly the
exact value at the envelope-selected scale. It does show that once a Tier-B row
is paid for, Tier C is numerically trustworthy and cheap to choose.

## The 15-second path fails

Device-fold warm steps range from `4.822 s` to `8.805 s`. Individual complete
Tier-B rows are highly heterogeneous: median `200.410 ms`, but the frozen
per-target maxima range from `3.894 s` to `7.142 s`. Conservative capacity is
therefore:

| K | Targets |
|---:|---:|
| 0 | 2 |
| 1 | 4 |
| 2 | 6 |

The structurally scheduled live slice captures only
`0.0000017823` of pooled oracle value (`0.000178%`). Its clairvoyant best row
inside K is also effectively zero on every target. Oracle schedule positions
range from 10 to 146, so better ranking inside the current first one or two
rows cannot rescue this design. The candidate-selection budget, not the exact
certificate, is the blocking vertebra.

This does not imply that every row costs several seconds: the median is much
lower. It does mean the preregistered worst-case-safe fixed-K rule cannot
exploit that heterogeneity. Any cumulative or cost-aware deadline scheduler is
future work and cannot be claimed from these opened labels.

## Decision

Accept the fresh result and reject the present complete-tree live B-to-C path.
Do not tune the structural schedule, replace worst-case K with a label-informed
rule, or advertise the pooled opportunity as deployable from this corpus.
Do not pursue another nearby DCFR variant or GPU micro-optimization as the next
step.

The next prerequisite is a continuation-root h32 representation beginning
after the observed public prefix, with the conditioned belief, updated pot and
commitments, legal remaining actors/actions, and the immutable blueprint
restricted to reachable descendant information sets. This change addresses
both problems revealed here:

- it removes decisions the bot can no longer make, restoring causal scope; and
- it should sharply reduce warm-step and candidate-library work before any new
  selector optimization is considered.

Preregister continuation-root equivalence and mutation controls before any
new strategy label. At minimum, prove public-history legality, pot/stack and
terminal-payoff identity, blueprint restriction identity, conditional reach
normalization, descendant-only block membership, and exact agreement with a
full-tree conditional evaluator on reduced games. Preserve the 15-second
reserve, immutable fallback, and ADR-0179 numerical ceilings.

No strategy is populated. This result makes no deployed strategy-quality,
continual-resolving, population, composition, or broad poker-strength claim.
