# ADR-0099: Preregister h32 real-blueprint warm-search acceptance

**Status:** Frozen before any shifted h32 blueprint or warm-search quality
label

**Date:** 2026-08-20

## Decision

Run the first strategy-facing h32 acceptance experiment from the exact
iteration-64 average blueprints accepted in ADR-0098. Apply two deterministic,
positive, support-preserving belief shifts to each of the balanced and
blocker-heavy source beliefs. Warm-start full-tree DCFR from the real blueprint,
measure average candidates after one, two, and four iterations, and compare
blind, aggregate-exact, and all-six-seat unilateral-non-worsening deployment.

The frozen config is
`experiments/configs/h32-warm-search-acceptance-v1.json`, SHA-256
`b5cbc538d51f09aad5aa6dca6c860865afd849196b65560ea3338d83293d7f8d`.
The runner is
`src/pontius/h32_warm_search_acceptance_audit.py`, SHA-256
`b0d48b0ca34e5153ea8317133bca96a32fd9ea57fcbe539e958fedddcae5870f`.
The result target is
`experiments/results/h32-warm-search-acceptance-v1.json`.

Immutable policy sources are:

- ADR-0092 ladder, SHA-256
  `242de5f0a42693248f98cc8f127f4fc892606df58e94d28c107d542b1276736b`;
  and
- ADR-0098 extension, SHA-256
  `cf2e2d85bfc8a5dd49f9490b7ddcac2817eaf9d73d9857535a72ac8e964f5ce9`.

ADR-0096's width artifact is also pinned at SHA-256
`5e34cb54f0be353320d1190ca0cce504fce327693f9d3de47d29a33350d471c5`
and must still select width 384.

## Question

The wide engine now trains a strong policy, but that is not yet the project
objective. The missing strategy question is:

> When the operative multiway belief moves away from the blueprint belief,
> does a very small amount of warm search create enough exact, conservatively
> acceptable quality to justify spending online decision milliseconds on
> search and verification?

This experiment tests strategic value, not a production latency claim. It is
the dense-free h32 analogue of ADR-0054, narrowed to four target cases so one
developer can falsify the architecture cheaply.

## Frozen target beliefs

For each of the two source factor beliefs, build two target beliefs over the
identical 32-hand axes and three mixture components.

### Local blocker shift

Fix target seat three. Count how often each card in each of its hands appears
on all opponent hand axes. Select the hand with maximum combined overlap,
breaking ties by stronger river showdown rank and then the smallest canonical
hand. Multiply that hand's unary likelihood by exactly `2.0`; every other
likelihood remains `1.0`.

This is a sparse blocker-sensitive perturbation. Selection uses only cards,
board strength, and source axes—never a policy or future quality label.

### All-seat strength shift

Within each seat, map exact lexicographic seven-card rank tuples to ordered
integer strength levels. Assign likelihood `1 + level/(levels-1)`, ranging
from exactly `1.0` to `2.0`. Equal ranks receive equal likelihood. Apply all
six positive unary likelihood vectors.

This is a dense but still exactly factorized shift. It does not introduce a
joint alignment factor or expand mixture rank.

Both shifts preserve every positive source assignment and reuse the exact card
topology, CSR maps, structured terminal automata, public tree, hand order, and
information schema. Only the belief component products and partitions are
recompiled.

## Pre-freeze target diagnostics

Target construction was exercised before strategy labels. Exact rank-one open
mode marginal reads report mean per-seat marginal TV:

| Family | Local blocker | All-seat strength |
|---|---:|---:|
| Balanced | 0.008188 | 0.072099 |
| Blocker-heavy | 0.004234 | 0.070051 |

The complete target workspace plus marginal-control path took 134-147 ms per
case. All schemas contain 6,144 information sets. Reconstructed source-policy
digests are exact. Warm-started current policies differ from the supplied
blueprints by at most `2.22e-16`, with mean TV about `3.2e-17`.

These are disclosed range/mechanism facts, not strategy labels. No shifted
blueprint NashConv, candidate policy, warm-search gain, acceptance label, or
h32 search timing was observed before freeze.

## Frozen policy matrix

The operative blueprint is iteration-64 average. Evaluate two real checkpoint
controls under every target belief:

- iteration-32 average, representing the weaker stable source; and
- iteration-48 current, representing the sharp low-NashConv source candidate.

Neither control can replace the fixed primary search candidate.

Initialize a pristine target-belief DCFR solver from iteration-64 average with
pseudo-regret mass `0.1 * payoff_span = 3.0`. Run exactly four alternating
iterations. Evaluate and serialize the average policy after iterations one,
two, and four. The fixed primary candidate is average iteration four; earlier
checkpoints are preregistered diagnostics and sequential-incumbent candidates.

All checkpoint states retain literal regrets, strategy sums, current/average
policy digests, target provenance, and canonical JSON state digests.

## Exact quality and acceptance semantics

Evaluate the blueprint and all five candidates with the exact dense-free
six-seat leaf-adjoint evaluator under the target belief. Let the normalized
guard be `1e-10`, or raw guard `3e-9` on this payoff span.

For every candidate relative to the target-belief blueprint:

- blind always deploys;
- aggregate exact deploys only when raw NashConv falls by strictly more than
  the guard; and
- unilateral Pareto additionally requires that no seat's deviation gain rises
  by more than the raw guard.

Ties inside the aggregate guard abstain. Rejected candidates deploy the
blueprint and receive zero quality reduction. The term “Pareto” applies to the
six deviation-gain constraints, not player utilities or coalition value.

Independently replay aggregate and unilateral best-so-far incumbents across
warm averages one, two, and four. Each comparison is relative to the currently
accepted incumbent, not permanently to the cold blueprint.

No coalition arm is included. Six-player coalition enumeration is an offline
stress program, not a plausible runtime acceptance target, and would confound
the first wide strategic test.

## Honest cost bills

For the fixed iteration-four candidate, record:

- blind: cumulative four-step search only;
- verified precompiled: search plus candidate exact evaluation, assuming the
  target-belief baseline vector is already cached;
- verified one-shot: target belief workspace compilation, baseline exact
  evaluation, search, and candidate exact evaluation; and
- the family-level support-topology/GPU upload separately, because it is
  reusable across support-preserving targets.

The exact teacher is expected to take tens of seconds. Report normalized
reduction per millisecond anyway and solve the pooled verifier break-even bill.
Do not call the teacher online-ready if it happens to pass a rate comparison.

The signed clean-fringe reader is deliberately excluded. It is proven only
where a policy-conditioned TT cache can be built; no such h32 cache has passed.
Forcing it into this experiment would mix strategic value with a new
representation claim. If safe search value survives, building the fixed-belief,
varying-policy h32 gate becomes the next justified systems customer.

## Frozen mechanism gates

The audit passes only if:

- four target rows, two per family, are present;
- every target has five candidate rows and three warm-search candidates;
- every search reaches iteration four and identifies average four as primary;
- all geometries retain 6,144 information sets and 12,288 hand-action entries;
- every balanced training/evaluation profile uses 435 terminal batches and
  every blocker-heavy profile uses 311;
- all three source policies reconstruct to their frozen digests;
- hand axes and support remain identical and every likelihood family spans
  exactly `[1.0, 2.0]`;
- minimum mean marginal TV is at least `1e-6`;
- warm-start error is at most `1e-12` per probability and `1e-13` mean TV;
- all search checkpoint state digests replay exactly;
- maximum step, exact evaluation, and target workspace compilation are at
  most 60, 60, and 30 seconds;
- host numeric and CuPy-pool peaks stay at or below 3 GB and 4 GB;
- maximum six-seat zero-sum residual is at most `1e-9`;
- all policies, states, and quality outputs are finite; and
- complete wall time is at most 1,800 seconds.

There is no quality, acceptance-rate, rate-win, policy-ordering, or selected
checkpoint gate. A strategically negative result can and should pass when
measured correctly.

## Frozen hypotheses

Report these independently of the mechanism pass:

1. pooled blind iteration-four normalized reduction is positive;
2. aggregate exact precompiled reduction per millisecond exceeds blind;
3. unilateral Pareto accepts at least one of four primary targets; and
4. unilateral Pareto deployed normalized reduction is positive.

The four-case sample is a development falsification, not a transfer estimate.
No hypothesis authorizes fitting a target selector.

## Validation before freeze

Five new tests pin the immutable matrix and outcome-neutral gates, construct
both likelihood families on reduced axes, test aggregate versus unilateral
labels, and verify source-relative sequential incumbents. A complete h4
orchestration control produced all five candidates, four search steps, exact
checkpoint identities, a finite primary result, and warm-start probability
error `1.11e-16`.

The final full repository/GPU regression is required before execution.

## Interpretation branches

1. **Blind search is nonpositive:** the strong blueprint or tiny action tree
   leaves no useful four-step adaptation. Resume blueprint work or widen the
   strategic game before optimizing an acceptance reader.
2. **Aggregate improves but unilateral rejects:** search redistributes
   vulnerability across seats, reproducing the core ADR-0056 multiplayer
   problem. Keep the vector gate; do not optimize aggregate-only deployment.
3. **Unilateral-safe value survives but teacher rate loses:** accept strategic
   search as a product customer and build the h32 fixed-belief policy-delta
   verifier. The measured break-even bill becomes its gate.
4. **Safe value and exact rate both survive:** still treat the leaf evaluator
   as an offline baseline; profile a resident/fused successor against the full
   bill rather than declaring seconds-scale evaluation deployable.
5. **Controls beat warm search:** inspect whether checkpoint provenance, not
   new solving, is the efficient customer. Do not select a control post hoc.
6. **Mechanism gate fails:** reject all downstream strategic interpretation.

## Limitations

The shifts are deterministic laboratory perturbations, not posteriors from a
real opponent model or observed public action. The public tree remains one
fixed bet on one river board with equal stacks. Only two generated range
families and four targets are measured. NashConv is unilateral reduced-game
deviation gain, not coalition safety, six-max equilibrium proof, or expected
casino win rate.

## Dissent protocol

**Confidence:** very high in target/source identity and exact evaluation;
high that the experiment isolates strategic value; low-to-moderate that four
warm iterations improve an already strong blueprint under every shift.

**Opposing evidence:** ADR-0056 found early warm search valuable in a smaller
three-player game, but the h32 blueprint residual is now only about `0.00186`.
The artificial shifts create adaptation headroom, yet full-tree warm DCFR can
still oscillate or move one seat's error into another.

**Largest risk:** four handcrafted cases overstate consistency. Passing would
justify a broader grouped workload after the hot-path mechanism exists, not a
runtime selector.

**Cheapest falsification:** the local-blocker balanced target. It is the
smallest measured shift; a harmful or unverifiable primary candidate there
immediately challenges the claim that four-step search is a robust default,
while the frozen audit still runs all cases.
