# ADR-0054: Preregister multiway full-search and acceptance development matrix

**Status:** Accepted before context construction or strategy labels

**Date:** 2026-08-19

## Decision

Run the first grouped three-player `MultiwayRiverHoldem` strategy experiment.
The experiment asks whether full-tree warm search has positive value after
multiplayer quality is constrained progressively by aggregate NashConv,
per-player unilateral deviation gains, and pair-coalition stress. It does not
fit a scheduler, prune actions, claim multiplayer safety, or optimize the
explicit joint-deal representation.

The frozen configuration is
`experiments/configs/multiway-river-search-acceptance-development-v1.json`.
Its SHA-256 is
`511303952baa67bdde3824fca3b6f59099e8270dd9f799e4ac73643c0253244f`.
The result target is
`experiments/results/multiway-river-search-acceptance-development-v1.json`.

## Grouped workload

Request eight deterministic board groups using seed `20261220`. The existing
hash splitter assigns entire groups to development, validation, or test; pass
only `development` into generation. The configuration requires six development
groups. Validation and test cards or ranges must never be constructed.

Every retained board produces four source range families with three private
hands per seat:

- `balanced`: all seats sample across the showdown-strength distribution;
- `polarized`: seats zero and two sample low/high tails while seat one remains
  balanced;
- `blocker_stress`: later seats preferentially select cards appearing in
  earlier seats' candidate hands, subject to every private hand retaining at
  least one compatible joint deal; and
- `correlated`: balanced supports receive explicit three-way assortative joint
  weights rather than a product distribution.

Pot, one fixed bet, and equal stacks are selected only from the frozen options.
All variants of one board share structure and split. Context features may use
cards, exact source ranges, compatibility, entropy, conditional range shifts,
hand strength, pot geometry, and player seat. They may not use CFR results,
future policies, exact deviation gains, coalition gains, acceptance decisions,
or family/split identifiers as a deployment signal.

## Target range shifts

Construct four support-preserving target ranges from every source context:

1. for each seat independently, find the private hand whose conditional joint
   distribution over the other seats has maximum total variation from their
   unconditional joint distribution; multiply deals containing that hand by
   exactly `2.0`; and
2. apply a three-way showdown-strength alignment likelihood ranging linearly
   from `2.0` when all three within-seat rank indices agree to `1.0` when their
   index spread is maximal.

Renormalize once after each likelihood. Ties in maximum conditional shift use
canonical hand order. No support addition/removal is permitted. Record root TV,
per-seat marginal TV, expected and maximum conditional-other-range TV,
reweighted hand identity/strength, compatibility, entropy change, and the exact
likelihood extrema before solving. These are causal boundary features, not
selection rules.

## Source blueprint and full search

Solve every source context with full-tree DCFR. At checkpoints 128, 256, and
512, choose the first average policy whose exact NashConv divided by the game
payoff span is at most `0.001`. Failure by 512 is a declared source-quality gate
failure; do not switch solvers or relax the threshold.

Evaluate the source blueprint unchanged under each target range. Then warm-start
full-tree LCFR, CFR+, and DCFR from that policy with pseudo-regret mass
`0.1 * target payoff_span`. Record average policies after 1, 2, 4, 8, 16, and
32 cumulative iterations. Every solver sees the complete fixed-bet action tree.
No exact label affects solver construction, stopping, or output.

The fixed primary candidate is average-policy DCFR at iteration 32. Other
solver/checkpoint rows are diagnostic comparisons and cannot replace the
primary gate after results are visible.

## Four deployment arms

For every candidate, evaluate four arms against the target-range blueprint:

1. `blind`: deploy the candidate without a quality gate;
2. `aggregate_exact`: deploy only if NashConv falls by more than
   `1e-10 * payoff_span`;
3. `unilateral_pareto`: additionally require that no player's deviation gain
   rises beyond that guard; and
4. `coalition_stress`: additionally require that none of the three exact pair-
   coalition gains rises beyond that guard.

The last two labels use the frozen ADR-0052 definitions. They are operational
incumbent comparisons, not equilibrium or collusion-safety theorems. Ties and
numerical ambiguity choose the source blueprint.

## Exact evaluation and timing

Compile one policy-parameterized dependency tape per target at the baseline
policy. Compare every candidate with complete ordinary traversal and dense hot
tape evaluation, including exact best-response action maps outside timing.
Record compilation separately.

Charge:

- blind search: cumulative solver time only;
- ordinary aggregate/unilateral acceptance: solver plus ordinary exact
  evaluation;
- hot aggregate/unilateral acceptance: solver plus hot tape evaluation, with
  compilation reported both one-shot and amortized over the trajectory; and
- coalition acceptance: solver plus hot unilateral evaluation plus exact
  candidate coalition evaluation, with baseline coalition evaluation and tape
  compilation separately visible.

Teacher evaluation, feature construction, serialization, and analysis remain
offline unless explicitly included in one of those charges. Use deterministic
state work alongside wall time so noise cannot determine the strategic verdict.

## Frozen gates and branching verdicts

Correctness/mechanism gates require:

1. six development groups and no materialized reserved context;
2. every source normalized NashConv at most `0.001`;
3. ordinary/tape evaluation error at most `1e-10`, zero best-response action
   mismatches, and exact source-relative replay;
4. every unilateral-Pareto deployment to satisfy its per-player constraints;
5. every coalition-stress deployment to satisfy all declared pair constraints;
6. aggregate hot evaluation to be strictly faster than ordinary evaluation;
   and
7. compile plus two hot candidates to be strictly faster than two ordinary
   candidate evaluations.

The fixed primary strategic hypotheses are evaluated independently:

1. aggregate exact acceptance strictly exceeds blind DCFR-32 raw NashConv
   reduction;
2. after hot verification cost, it strictly exceeds blind DCFR-32 raw
   reduction per millisecond;
3. unilateral-Pareto accepts at least 10% of primary targets;
4. coalition-stress accepts at least 5% of primary targets; and
5. coalition-stress deployment has positive aggregate payoff-normalized
   NashConv reduction.

Failure of a strict arm does not invalidate the exact game. Instead:

- if blind full search has nonpositive aggregate value, enrich the game before
  optimizing its representation;
- if aggregate acceptance helps quality but loses rate, retain it as a teacher,
  not an online gate;
- if unilateral or coalition acceptance almost never fires, retain the raw
  diagnostic and reject that strict rule as a practical incumbent; and
- only if useful search value survives at least one conservative arm does exact
  factorized/low-rank belief contraction advance as the next scaling project.

No threshold, solver, checkpoint, family, target, or gate may be changed after
the first strategy label is inspected.

## Dissent protocol

**Confidence:** high in the correctness comparison; moderate that full warm
search improves shifted ranges; low that pair-coalition non-worsening accepts
often enough to be practical.

**Opposing evidence:** multiplayer CFR lacks the heads-up equilibrium guarantee,
the source quality threshold is empirical, and one fixed bet may make nearly
all reasonable policies look similar. Conversely, the shared-card coalition is
deliberately stronger than ordinary independent opponents and may reject good
unilateral policies.

**Largest unknown:** whether strategy gain survives the transition from one
aggregate number to six explicit constraints—three unilateral and three pair
coalition gains.

**Cheapest falsification:** this 24-context development workload. The fixed
DCFR-32 arm and all strict acceptance rules are declared before any context is
solved.
