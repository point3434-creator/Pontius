# ADR-0069: Preregister guarded incremental policy-delta TT recomposition

**Status:** Accepted before cache implementation, delta timings, or labels

**Date:** 2026-08-19

## Decision

Correct the reuse axis exposed by review and ADR-0068. The acceptance path holds
the belief fixed while evaluating many candidate policies. Cache every
public-node TT for a baseline policy, then recompose only policy-changed nodes
and their unique ancestor closure.

The frozen configuration is
`experiments/configs/policy-delta-tt-recomposition-audit-v1.json`. The result
target is
`experiments/results/policy-delta-tt-recomposition-audit-v1.json`.

This audit has two goals which must remain separate:

1. measure composition-amortized-per-candidate for localized policy changes;
2. turn tolerance-only rounding diagnostics into a conservative acceptance
   guard, including an explicit Float64 machine-noise term.

It cannot rehabilitate the rejected fixed rank caps from ADR-0068.

## Two products, two authorities

The capped/compressed product is authorized only for value estimation,
scheduling, prioritization, and approximate search. Its ADR-0067 tolerance was
`1e-4` of payoff span, six orders looser than the acceptance comparator's
`1e-10 * span`. No capped result may feed acceptance or certification even if a
later value screen passes.

The tolerance-only product may feed guarded acceptance only when the estimated
improvement exceeds all of:

- the baseline root error bound;
- the candidate root error bound;
- a separate Float64 machine-noise allowance; and
- the existing `1e-10 * payoff_span` acceptance tolerance.

Otherwise it abstains. This semantic division is part of the frozen contract,
not a downstream convention.

## Cached composition

For every public node store:

- its rounded TT;
- its hand/action policy probability tensor, if strategic;
- its local discarded Frobenius bound;
- its propagated root-value sup-norm bound; and
- its parent index.

The public game is a tree. A change at one public node dirties that node and one
ancestor path. A whole-seat change can touch many public nodes, so its dirty set
is the union of their ancestor paths, not necessarily depth-many nodes. Report
both changed-node and closure counts; do not describe whole-seat updates as a
single path.

Recompute dirty strategic nodes in reverse topological order using candidate
policy unaries and candidate child TTs. Unchanged subtrees retain object-identical
cached TTs. A cold control recomposes all 385 nodes from the same terminal TT
library and rounding settings.

## Bound propagation

At a fixed-policy node,

`V = sum_a pi(a|h_i) V_a`, with `pi >= 0` and `sum_a pi = 1` pointwise.

If child `a` has a certified sup-norm error bound `b_a`, their policy-weighted
sum has error at most `max_a b_a`. TT rounding adds a local residual whose
sup norm is no larger than its discarded Frobenius norm `d`. Propagate

`b_node = max_a b_child(a) + d_node`.

This accumulates along the worst root-to-terminal path, not across all 385
nodes. Terminal rounding contributes its own discarded bound.

The SVD discarded bound covers truncation, not Float64 QR/SVD/multiplication
noise. Add a distinct allowance

`epsilon * 256 * public_tree_depth * payoff_span`

to every guarded comparison. The multiplier is frozen as a conservative
engineering allowance, not claimed as a formal backward-error proof. The
existing `1e-10 * payoff_span` tolerance remains separate and larger.

## Zero-sum coherent-error alarm

Compose all six player operators in the tolerance-only arm. Under the same
belief, report

`abs(sum_i estimated_utility_i)`

and compare it with the sum of all six root bounds plus machine noise. The true
terminal game is zero sum. A residual outside this envelope indicates broken
payoff grouping, axis alignment, or coherently underestimated rounding error.
This is an alarm, not a substitute for per-player dense-oracle checks.

## Frozen workload

Use four and seven hands per seat, balanced and blocker-heavy axes, one fixed
three-component belief per case, and all six target players. The baseline is
the deterministic hashed-dense policy.

Generate five deterministic candidates:

1. swap one hand's two action probabilities at the root;
2. swap one hand at the deepest lexicographically first strategic node;
3. swap every hand at that one deepest node;
4. swap every information-set distribution controlled by seat 3; and
5. replace the full profile with a separately seeded hashed-dense policy.

The first three isolate a single ancestor path. The fourth measures the actual
single-seat acceptance customer. The fifth is a full-dirty diagnostic and is
not expected to gain from incremental recomposition.

For each candidate and player:

- compare incremental and cold root tensors;
- compare both with the independent dense public-tree root;
- contract against the unchanged exact belief;
- report changed nodes, dirty closure, cache bytes, incremental and cold time,
  root bounds, actual error, and bound slack.

Across all six players, report zero-sum residual, aggregate cold/incremental
candidate time, guarded sign certificates, abstentions, and false certificates.

## Amortized candidate economics

The baseline cache is a compilation cost. For reuse counts `1,2,4,8,16`, report

`incremental_candidate_time + baseline_cache_compile_time / reuse_count`.

The single-seat candidate must be strictly faster than cold recomposition at
four reuses after this charge, pooled across the four geometry cases. Report
every case separately. Single-node cases are diagnostics for the best possible
locality; the full-policy candidate is the no-reuse structural control.

## Frozen gates

Require:

- maximum incremental-versus-cold root tensor error at most `1e-10`;
- maximum incremental-versus-dense utility error at most `1e-8`;
- no actual root error exceeding its truncation plus machine-noise envelope;
- no six-player zero-sum residual exceeding the summed envelope;
- zero false guarded positive or negative sign certificates;
- every one-node mutation's dirty set equals that node plus its ancestor path;
- pooled single-seat four-reuse amortized time strictly below cold time; and
- all six player utilities present in every zero-sum diagnostic.

Failure of a speed gate rejects cache economics, not TT correctness. Failure of
a bound or zero-sum gate blocks any acceptance authority.

## Interpretation branches

- If incremental/cold identity fails, fix dirty closure or cache invalidation.
- If bounds fail, the discarded-norm propagation is not certification-ready;
  retain exact dense/tape acceptance controls.
- If one-node updates win but whole-seat fails, cache reuse serves local search
  edits but not unilateral acceptance.
- If whole-seat passes, use incremental tolerance-only composition as the
  acceptance evaluator while the guard clears; keep capped value models
  separate.
- Regardless of outcome, build dense-free showdown terminals before claiming a
  32-hand path.

## Dissent protocol

**Confidence:** very high in dirty-tree semantics and cold identity; high in
the convex bound recurrence; moderate in measured cache economics; low that the
engineering machine-noise multiplier is a formal certificate.

**Opposing evidence:** caching all six players' node TTs may consume enough
memory to erase latency gains. Whole-seat changes may dirty most ancestors.

**Largest risk:** calling a truncation bound plus heuristic machine allowance
mathematically exact certification.

**Cheapest falsification:** an observed dense-root error or zero-sum residual
outside the reported guard.
