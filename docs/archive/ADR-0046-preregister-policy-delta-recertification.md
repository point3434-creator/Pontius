# ADR-0046: Preregister exact policy-delta recertification

**Status:** Accepted before implementation and measurement; passed in ADR-0047

**Date:** 2026-08-19

## Decision

Parameterize the generic Float64 dependency tape by behavioral-policy
probabilities as well as root probabilities, then run one frozen,
development-only mechanism test on the already revealed selective-expansion
matrix. The test asks whether an exact accept/no-op gate can update a solved
candidate policy more cheaply than ordinary full evaluation without changing
any evaluation, best-response action, or acceptance decision.

The frozen configuration is
`experiments/configs/policy-delta-recertification-development-v1.json`, SHA-256
`4653662e585b053d8bb8b11400249069b5d289c210807aad78e87ecdaabbda0e`. The result target is
`experiments/results/policy-delta-recertification-development-v1.json`.

This run cannot revive the rejected causal width selector, authorize a learned
selector, or supply fresh strategy-quality evidence. Its source labels were
revealed in ADR-0044. It is a paired correctness, invalidation-density, and
cost test only.

## Frozen source and candidate regeneration

Read only
`experiments/results/river-selective-expansion-development-v1.json`, SHA-256
`7571a8a2f3c08034b53982b4ac122106fbe3d1cc7b216d3ee4ba58cf01fdd2ff`.
Require its canonical config SHA-256 to equal
`3740d5a9ae9293eb71bdc3a6491cf6b5e22d40289918534755c0a414ce46e3d9`,
its implementation commit to equal
`e0ff3a6621449d5e06060395516c037e676ce6df`, and its counts to be eleven board
groups, 44 contexts, and 132 range targets.

The artifact stores labels but not policies. Deterministically regenerate each
target blueprint and only two candidates from its embedded configuration:

- near-full `b3r1` and full `b3r2`;
- warm-start mass `0.1 * target payoff span`; and
- budget 32 full-tree-equivalent iterations.

Before using a regenerated candidate, match its baseline NashConv, candidate
NashConv, and reduction against the frozen row within `1e-10`. A mismatch is a
provenance failure, not a new observation to be explained away.

The 132 full `b3r2` candidates are primary because ADR-0044 identified exact
accept/no-op on that fixed search as the actionable opportunity. The 132
`b3r1` candidates are a secondary cone-density control. No mask, warm mass,
budget, threshold, or subset may be selected after seeing the new timings.

## Policy-input semantics

Compile exactly one input for every materialized `(information-set, action)`
probability and reuse that input at every concrete history in the information
set. Validate action consistency, finiteness, nonnegativity, completeness, and
normalization. An omitted policy information set has the evaluator's existing
uniform semantics only when the complete source policy is first materialized;
candidate updates themselves must provide the complete compiled schema.

Fixed-policy utility circuits depend on every acting player's policy inputs.
For a best response by player `i`, opponent and chance continuations depend on
their probability inputs, while player `i`'s own behavioral inputs must not
enter that best-response circuit. Information-set argmax selectors remain
global and bottom-up.

Every recertification is source-relative. Candidate B after candidate A is not
a delta from A. Unchanged entries retain immutable source values, and returning
to the source policy must be an exact identity operation. Changed entries use
the frozen `1e-15` comparison tolerance only for invalidation; all arithmetic
and comparisons remain Float64.

## Independent controls

For every candidate, compare sparse, dense, and automatic tape execution with
the existing object-tree `evaluate_profile` and independently reconstructed
best responses. Run candidates in forward order, reverse order, repeat the
first candidate after the other candidate, and return to the source policy.

Automated tests must additionally cover:

- identity, one-information-set, and multi-information-set policy changes;
- a policy change that flips a best-response action;
- incomplete, unknown, negative, nonfinite, and unnormalized policies;
- multiplayer unilateral best responses;
- positive payoff scales `0.5`, `1`, `2`, and `4`;
- deterministic no-op behavior inside the payoff-scaled acceptance tie band;
  and
- record-order invariance of aggregate acceptance results.

The acceptance rule deploys the candidate only when

`baseline NashConv - candidate NashConv > 1e-10 * payoff span`.

Otherwise it deploys the incumbent blueprint. Full and incremental decisions
must agree exactly under this rule. This conservative band prevents numerical
noise near a literal tie from masquerading as strategy quality.

## Frozen timing protocol

Compilation, hot policy updates, and ordinary full evaluation are timed
separately. Warm each path once, then take the median of seven paired
measurements, alternating which path runs first by record and repetition. Do
not include JSON serialization, candidate regeneration, best-response action
reconstruction, or correctness-only sparse/dense duplicates in the hot timing.

The primary rate calculation uses payoff-normalized NashConv reduction summed
over all 132 full candidates:

- **blind full:** literal signed candidate reduction divided by solve time;
- **ordinary exact gate:** accepted positive reduction divided by solve plus
  full-evaluation time;
- **hot tape gate:** the same accepted reduction divided by solve plus hot
  policy-update time; and
- **compile-charged tape gate:** the same accepted reduction divided by solve,
  tape compilation, and hot update time.

Candidate solve times are freshly measured during deterministic regeneration.
The ordinary and tape gates must make identical decisions, so any quality
difference is a correctness failure. Compilation is never silently amortized.

## Frozen gates and verdict hierarchy

The run passes its core contract only if:

1. maximum absolute error across utilities, best-response values, deviation
   gains, NashConv, and exploitability is at most `1e-10`;
2. regenerated source and candidate labels match the frozen artifact within
   `1e-10`;
3. sparse, dense, and automatic best-response actions exactly match the
   independent evaluator, with zero acceptance-decision mismatches;
4. all dependencies remain topological and source-relative replay, identity,
   order, payoff-scale, and tie controls pass;
5. aggregate median hot policy-update time is strictly less than aggregate
   ordinary full-evaluation time; and
6. hot verified normalized reduction per millisecond strictly exceeds blind
   full search.

The exact inequalities are represented by a configured minimum ratio of `1.0`;
equality fails. Do not substitute a favorable mean, selected subset, raw-chip
rate, or earlier recorded timing if a frozen median/normalized gate fails.

The compile-charged rate is a mandatory reported classification, not a hidden
amortization and not a core gate. If it beats blind search, this Python control
supports cold online feasibility. If only the hot rate passes, evaluator reuse
or precompilation is required. If the hot update does not beat full evaluation,
the parameterized tape adds no demonstrated value over the already working
exact evaluator even when exact accept/no-op itself remains beneficial.

No dirty-fraction threshold is a pass gate. Report changed policy entries and
information sets, dirty and recomputed fractions, selectors affected, action
flips, and sparse/dense timing separately by mask. If most candidate cones are
dense, retain dense flat evaluation as the candidate architecture and stop
selling sparsity as the source of the win.

## Limits and next decision

This is still an explicitly enumerated, two-player river control. NashConv here
is the sum of unilateral deviation gains. It is neither coalition safety nor a
six-player equilibrium certificate. Python timing ranks mechanisms on this
workload; it is not an RTX/Zen native latency claim.

If correctness and hot economics pass, the next step is a compiled SoA kernel
benchmark with policy inputs and a compile-reuse study. If exactness fails,
repair the tape before any optimization. If exactness passes but hot economics
fail, use the ordinary exact evaluator as the teacher and move policy-delta
optimization behind a more scalable reduced-game or learned uncertainty gate.

## Dissent protocol

**Confidence:** high in the paired exactness test; moderate in the timing rank
within Python; low in direct transfer to six-player NLHE.

**Opposing evidence:** online CFR changes most reached information sets, global
best-response selectors may make its dependency cone nearly dense, and a tape
compile can cost more than simply evaluating the candidate once.

**Largest unknown:** whether shared policy inputs localize enough downstream
work to outperform a dense bottom-up pass after realistic candidate movement.

**Cheapest falsification:** zero numerical disagreement but hot update time at
or above ordinary full evaluation, or dirty fractions near one for both frozen
candidate masks.
