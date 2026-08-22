# ADR-0227: Preregister the live-like continuation strategy trial

- Status: accepted preregistration
- Date: 2026-08-22
- Follows: ADR-0226
- Experiment: `experiments/configs/h32-continuation-root-strategy-trial-v1.json`

## Context

ADR-0226 moved the continuation path out of selector scarcity. All 31 legal
post-action public-node blocks fit the deterministic cumulative ledger on all
12 frozen targets, and conservative worst-case K is at least nine. The next
question is no longer whether a proxy can locate one block inside an
unaffordable library. It is whether the complete affine proof can select and
independently deliver exact safe value on the causally correct continuation
tree before the street deadline.

This is the first fresh continuation strategy trial. It does not reopen the
complete-tree labels from ADR-0222 and it does not use the ADR-0226 timing rows
as opportunity features. Those rows provide only each target's frozen maximum
candidate cost for a hard pre-candidate clock guard.

## Frozen feature phase

Use the same 12 source checkpoints, action-conditioned posteriors, exact public
prefixes, continuation automata, and immutable restricted blueprints as
ADR-0226. For each target:

1. run exactly one device-fold DCFR warm step;
2. enumerate the exact 31 public-node blocks and 992 information sets in
   continuation public-tree preorder;
3. before each block, require enough time before the 14-second cutoff for that
   target's ADR-0226 maximum complete candidate cost, 10 ms affine-envelope
   reserve, and 1,250 ms exact-certificate start reserve;
4. for each guard-admitted block, build its one-step regret vertex, compute the
   acting seat's zero-contraction row and five opponent-BR-conditioned rows,
   and form the complete selector-stable affine envelope; and
5. freeze the winner as the positive complete envelope with greatest predicted
   NashConv reduction, breaking exact ties by lowest public-tree schedule
   index.

There is no Tier-A exclusion filter, proxy score, family comparison, scale
search, or label-informed ordering. A target with no positive complete envelope
freezes blueprint abstention.

Complete every target's feature matrix and frozen winner while all independent
strategy labels and teacher rows are null. Only then open the teacher phase.

## Frozen teacher and clock semantics

Reconstruct each selected target's identical resident context and run exactly
one independent incremental certificate at the affine envelope's frozen scale.
Context reconstruction is experimental overhead required by the all-target
label barrier and is excluded from the simulated live clock; the live context
already exists at winner selection. The simulated live completion time is the
measured warm-plus-candidate feature clock plus the independent certificate's
wall time.

The shadow rule accepts the winner only if:

- the certificate start guard still has 1,250 ms before the 14-second cutoff;
- the independent proof completes by 14,000 ms;
- the proof is complete;
- exact NashConv reduction exceeds the inherited `2e-11` numerical allowance;
  and
- predicted and independently exact utilities, best-response values, and
  deviation gains agree within `2e-11`.

Any failure, lateness, abstention, or numerical disagreement selects the
immutable restricted blueprint. The repository artifact itself always emits
that blueprint; candidate selection is shadow research and cannot populate a
deployment strategy in this experiment.

## Frozen reporting and gates

Report per target: priced block count, stop reason, selected block and scale,
predicted value, exact delivered value, proof completeness, affine-teacher
error, simulated completion time, deadline usability, abstention reason, and
memory. Report pooled predicted and delivered exact value, accepted and
abstained target counts, and the full timing range.

Require all provenance, parent, source, target, blueprint, warm-start, complete
block-manifest, convex-scope, six-row charge, affine-intercept, hard-guard,
feature-label-barrier, independent-teacher, winner-selection, deadline-fallback,
memory, finite, and immutable-emission mechanisms. Strategy outcomes do not
gate experiment validity: no minimum positive value, acceptance count, or
deadline success is required.

## Decision rule

If the mechanism gates pass, interpret the fresh continuation result exactly
as observed:

- positive, exact, on-time winners establish delivered safe local value for
  these frozen action-conditioned continuation contexts;
- complete abstention establishes that this one-step regret-vertex family
  finds no value under the current envelope; and
- late or incomplete winners return the question to scheduling or certificate
  engineering without weakening fallback safety.

Any validity failure rejects the trial. Do not repair, rescale, reorder, add a
direction family, or query a second candidate inside the same evidence
artifact.

No strategy is populated. This preregistration makes no deployment,
continual-resolving, composition, population, or broad poker-strength claim.
