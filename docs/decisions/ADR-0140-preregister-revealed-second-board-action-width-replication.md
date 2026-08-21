# ADR-0140: Preregister revealed second-board action-width replication

## Status

Frozen after ADR-0139 and before any original-board h32 two-size policy
construction, resident strategy step, or common-game action-width quality
measurement.

## Context

ADR-0137 accepted the first common-game action-width mechanism on board
`4h 6s Td Qh As`, but both arms abstained on all four targets.  It therefore
made no action-width ranking.  ADR-0139 then established that the accepted
scale-canonical cache is memory-safe on board `2c 7d 9h Js Qc`, with all eight
one-size/two-size cache rows leaving the conservative non-cache reserve.  The
cache preflight executed zero h32 steps, policies, or quality evaluations.

The independent review correctly prioritized scaling the board/range corpus
before further acceptance-contract evolution.  This successor follows that
advice while keeping the evidential limitation explicit: the board is new to
the sized comparison, but it is the original one-size h32 board.  Its one-size
source policies, target beliefs, and historical one-size candidate labels are
already revealed.

This is therefore a revealed-board replication of the action-width mechanism,
not an independent holdout and not population evidence.

## Disclosed prior evidence

The following facts were known before this freeze and are machine-bound in the
configuration:

- on this board, ADR-0106's complete 13-policy one-size union selected a
  non-blueprint policy for both local-blocker targets and the blueprint for
  both all-seat-strength targets; and
- on the first sized board, ADR-0137 recorded blueprint abstention for both
  arms on all four targets, with zero selected reduction.

Neither fact is a gate, target filter, candidate rule, stopping condition, or
quality threshold.  They are disclosures only.

## Frozen identities

The machine-readable contract is
`experiments/configs/h32-second-board-action-width-v1.json`, SHA-256
`15e99de5d5bc45a62de4d6e24a06bb1a6a9d29d863464756e6b95a2f8e4cc011`.
The additive runner is
`src/pontius/h32_second_board_action_width_quality_audit.py`, SHA-256
`74b47ab4160746646f6c7788bfe1a8a15e27bfb72716b6b7f26ce6ebca85f559`.
Its direct control is
`tests/test_h32_second_board_action_width_quality.py`, SHA-256
`0df2b3357c990233e2dec613025ba64c8781c82f046bd7ca711076e2076c8b52`.
The result target is
`experiments/results/h32-second-board-action-width-v1.json`.

The contract directly pins:

- ADR-0139 cache preflight result, config, and implementation;
- ADR-0099 warm-search result and config;
- the checkpoint ladder and extension that reconstruct the exact average-64
  source blueprints;
- ADR-0137's corrected action-width result and the original action-width
  config and implementation;
- ADR-0106's acceptance replay result and decision record; and
- the new runner and control test.

All referenced configs are reparsed through their strict validators.  Before
any sized h32 work, both average-64 policies must reconstruct to their frozen
digests and all four label-free target beliefs must reproduce:

| Target | SHA-256 |
|---|---|
| balanced / local blocker seat 3 | `0837fb176c0ef13260c14e230bfb04d79755cdd232b71eabef69b29a2e08ab1a` |
| balanced / all-seat strength | `587407ff8dea2e735aa68470933e4cd009f71bb147fd40561bfa89dd8290d7e7` |
| blocker-heavy / local blocker seat 3 | `a59d5c7efbd0fbc441d3986a83a0cf86f890d52cfb5d6a2f4de8d8d3acd708e5` |
| blocker-heavy / all-seat strength | `221b112ad4407a06ecee2511344f71df93d4469f1572d5ed8569295296c326aa` |

## Frozen workload

Reuse ADR-0134's common-game comparison without tuning it to either disclosed
outcome:

- board `2c 7d 9h Js Qc`, pot `12`, six equal stacks of `30`;
- one-size arm with bet `3` and raw resident caches;
- two-size arm with bets `(3, 6)` and scale-canonical resident caches;
- balanced and blocker-heavy range families;
- local-blocker-seat-3 and all-seat-strength target shifts;
- arm order `one/two, two/one, two/one, one/two`;
- DCFR with warm pseudo-regret mass `0.1 *` each solver's own payoff span;
- a `90,000 ms` construction-plus-planning clock, `35,000 ms` whole-step
  reserve, and eight-step ceiling per arm; and
- fixed seat verification order `0,1,2,3,4,5`.

The memory authorization is conjunctive across every ADR-0139 cache row.  If
that parent does not pass, does not report all-eight headroom safety, or records
any h32 strategy work, this runner stops before target construction.

Each arm emits the same frozen label-free candidate stream:

1. current policy after complete step one;
2. behavioral alpha-0.50 interpolation of current steps one and two, if step
   two completes;
3. current policy at the deadline; and
4. average policy at the deadline.

Exact digest duplicates are merged, every sized policy round-trips through the
compact schema-bound representation, and neither arm sees exact quality during
planning.  Both arms finish planning before the target's first quality call.

## Common-game verifier

Both arms are evaluated in the same two-size game with layout-derived payoff
span `48`.  One-size policies are embedded by assigning zero opening mass to
bet `6`; below that off-tree action they copy the bet-`3` continuation.

For each target, construct a fresh canonical verifier cache and certify the
embedded immutable average-64 blueprint over all six seats.  Verify each arm's
deduplicated candidates against that same fixed cap vector.  A candidate stops
when a seat exceeds its blueprint cap plus raw guard `1e-10 * 48`, or when its
nonnegative partial NashConv cannot beat the best complete feasible candidate
within the same guard.  The fixed-envelope selector retains the blueprint on
guard ties.

Report planning, marginal-decision, and full-one-shot costs separately.  Exact
quality work is never hidden inside the arm clock.

## Frozen gates

The audit passes only if:

1. every pinned source and strict parser reproduces from a clean Git state on
   the frozen NumPy, SciPy, CuPy, CUDA, driver, and compute-capability stack;
2. ADR-0139 passes, reports all-eight cache safety, and records zero h32
   strategy work;
3. both average-64 blueprints and all four target identities reproduce before
   sized h32 construction;
4. the h2 common-game bridge, cache, profile, exact-quality, zero-sum, compact
   round-trip, 385/763-node, 127-terminal-group, payoff-span, and 378-basis
   controls reproduce within their frozen Float64 bounds;
5. all four targets and eight arms execute in frozen order with exact h32
   information-set and hand-action widths;
6. every arm completes at least one whole step, no step exceeds 35 seconds,
   no charged arm exceeds 90 seconds, and no cache exceeds 120 seconds;
7. every candidate round-trips exactly and every policy and complete quality
   row is finite;
8. both arms finish planning before any target quality evaluation;
9. quality-vector sums, zero-sum residuals, and per-seat timings stay within
   their frozen bounds;
10. every selection remains inside the immutable blueprint caps, the GPU pool
    remains below 12 GB, and total wall time remains below 3,600 seconds; and
11. the top-level strategy-quality claim is null.

There is no gate on selected reduction, arm winner, added-bet use, candidate
feasibility, abstention count, relative efficiency, or any strategy direction.
The aggregate outcome is recorded explicitly as not a gate.

## Pre-freeze controls

Five direct controls pass.  They pin the outcome-neutral workload and prior-
evidence disclosures, reject source, target, disclosure, and gate mutations,
reproduce all four label-free target identities, reconstruct both exact
average-64 blueprints, and verify that ADR-0139 alone authorizes the run.

The complete repository passed 571 tests in `106.777 s`.  No original-board
h32 two-size policy, resident step, or common-game quality label was
constructed during validation.

## Decision branches

- **Mechanism failure:** preserve the artifact, make no quality interpretation,
  and repair only under a new preregistration.
- **Clean diagnostic outcome:** record both arms, cap decisions, abstentions,
  and costs exactly, while keeping the top-level strategy claim null.
- **Apparent one-size or two-size advantage:** treat it only as revealed-board
  replication evidence.  Do not change the action abstraction or advertise a
  strategy ranking from two boards.

Any broader action-width claim requires genuinely fresh boards and preferably
additional range families or target constructions frozen before their labels
exist.

## Dissent

**Confidence:** extremely high in source and target identity; high in memory
safety and common-game exactness; low that a revealed second board materially
identifies the population action-width effect.

**Opposing evidence:** the first sized board produced universal abstention, and
the current board's favorable local one-size labels are already known.  A
different result here may reflect board choice or the disclosed generator
history rather than action-width value.

**Largest risk:** the replication is mistaken for independent confirmation.
It expands sized-board coverage from one to two, but only one board was unseen
to the preceding one-size research path.

**Cheapest falsification:** run this frozen artifact once.  A source, target,
cap, step, or exactness failure rejects the mechanism; a coherent strategic
result remains diagnostic and claim-null by construction.
