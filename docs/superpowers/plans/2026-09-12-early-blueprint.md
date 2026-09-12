# Early-street blueprint reference and design experiment

**Goal:** Build and test a bounded, restartable six-player preflop/flop training
reference, and assess the supplied decomposition memo without promising poker
strength or deploying a bot change.

**Architecture:** External-sampling tabular MCCFR with a frozen policy per full
iteration. Compare ordinary increments with iteration-linear increments. Train
only preflop/flop rows, using the existing exact six-seat betting and card
engine. A named, frozen later-street continuation supplies sampled terminal
utilities. Separate continuation identity from algorithm identity. Recover from
validated immutable checkpoint generations. Export full action probabilities.

**Tech stack:** CPython 3.14.6, existing Pontius library, standard-library
reference data structures, pytest/unittest, ruff. Optimize or port only after
measuring. No external trainer modification, GPU dependency, live provider
adoption, commit, push, remote launch, or substantial training run.

**Spec:** User requests six-max cash without rake, initially equal stacks at
selected depths across 20–200 bb; later mixed stacks; 14 seconds computation and
one second emission. This experiment tests machinery locally, not the dual
EPYC's throughput or a completed 14-second solver. Exact public action history
and recalled private abstractions remain in information keys. Future/other
players' private cards never enter policy inputs. All six dealt hands remain
excluded from the runout after folds. SPR alone cannot identify a subgame.

## Shared interfaces and ownership

| Surface | Owner | Contract |
| --- | --- | --- |
| `sampled_cfr.py` | controller | `ExternalSamplingCFR(num_players, root_sampler, game_id, variant, seed, max_rows, max_nodes)`; string actions; existing GameState protocol; checkpoint state is JSON-compatible |
| `early_holdem.py` | adapter task | `EarlyHoldemGame(stack_bb, max_raises, continuation)` with `game_id`, `sample_root(rng)`, `state_for(deal, betting)`. Root returns a GameState with string actions, six-player bb utilities and only early-street decisions |
| `training_checkpoint.py` | checkpoint task | `save_checkpoint(root, payload, generation)` -> Path; `load_checkpoint(root, expected_identity=None)` -> payload; identity is payload['identity']; JSON payload, immutable generations, validated recovery |
| tests | each owner | Independent behavioral tests matching each owned module; controller alone edits cases.json |
| experiment and evidence | controller | One bounded dated runner, raw paired evaluation outcomes, immutable snapshots, separate strength/throughput/recovery statements |

For average strategy, perform one separate path per target player: sample that
player with the frozen current policy, all other players uniformly over legal
abstract actions, chance from its true distribution; add `w_t * sigma(I,a)` only
at the target's nodes. Under perfect recall the expected update equals the
desired own-reach-weighted contribution times a fixed infoset-dependent factor.
That factor cancels on normalization. Opponent sampling MUST remain fixed.
Ordinary uses w=1; linear uses w=iteration for both regret and average updates.
No naive multiplayer opponent-node averaging, clipping, pruning or regret merges.

## Tasks and verification

1. **Sampled CFR reference.** Write failing tests for deterministic resume,
   frozen updates, atomic capacity stop, exact small-game averaging expectation,
   and heads-up Kuhn convergence against exact best response. Implement simple
   FP64 reference accumulators and complete state export/restore. No sampled
   multiplayer Nash guarantee.
2. **Checkpoint generations.** Write failing tests for a fresh round trip,
   corruption of newest generation, partial staging writes, identity mismatch,
   non-finite numbers and immutable milestones. Implement file flush/fsync,
   checksummed state, atomic generation publication and directory sync on POSIX.
   A Windows process-interruption test is not a Linux power-cut durability test.
3. **Early hold'em adapter.** Write failing tests for 169 preflop classes, suit
   permutation invariance, hidden-card/future-card independence, distinct public
   contexts, legal action menus, six-seat chip conservation, and no turn/river
   decision rows. Use exact suit-canonical flop cards first to avoid unvalidated
   buckets. Frozen check/call and a visible-information betting continuation
   are sensitivity controls, not solved leaves. Action abstraction is explicit.
4. **Bounded experiment.** Compare cfr and linear with matched configurations,
   retained initial/final milestones, limits on rows, nodes and elapsed time;
   test restart equivalence and fixed-panel paired complete-hand evaluation.
   Report uncertainty and coverage, including non-improvements. Count actual
   bytes, visits and elapsed time, never infer full-scale memory feasibility.
5. **Review and deliver.** Independent specification/numerical review; run new
   tests and affected existing suites; ruff changed files; package patch, source,
   commands and a memo review in the user-facing outputs directory. Preserve
   current D:/Pontius and all earlier milestone identities.

## Memo decisions

Keep independently schedulable conditional flop jobs, shared continuation
contracts, real node/memory measurements, stack grid and fixed evaluation panel.
Test decomposition against a sampled baseline. Do not assume 2–3 outer sweeps
converge, full-range six-player flop solving is cheap, PCFR+ universally wins,
SPR identifies equivalent games, torn checkpoints are harmless, seed alone
makes parallel updates deterministic, or neural values are the settled design.
Public flop ranges have 1,176 combinations; 1,081 is a five-public-card count.
