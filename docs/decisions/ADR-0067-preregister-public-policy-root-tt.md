# ADR-0067: Preregister fixed-policy public-tree root-TT audit

**Status:** Accepted before TT algebra implementation, composition, or labels

**Date:** 2026-08-19

## Decision

Test whether a complete fixed six-player public betting policy can be compiled
bottom-up into one compressed root value operator per target player. Contract
that root operator once with the exact factorized card belief, instead of
running ADR-0066 independently over 64 terminal payoff groups.

The frozen configuration is
`experiments/configs/public-policy-root-tt-audit-v1.json`. The result target is
`experiments/results/public-policy-root-tt-audit-v1.json`.

This is a preregistered revealed-engineering audit. It may approve or reject
bottom-up fixed-policy TT composition. It cannot approve unilateral response
actions, resolving, CFR updates, a neural model, or online deployment.

## Algebra

At a strategic public node `n` controlled by seat `i`, the fixed-policy value
operator is

`V_n(h) = sum_a pi_n(a | h_i) V_child(n,a)(h)`.

The action probability is unary in one private-hand axis. Multiplying it into a
TT therefore changes only core `i`. Exact TT addition concatenates first/last
bonds and block-diagonalizes intermediate cores. Immediately round the sum by
left QR orthogonalization and a right-to-left Float64 SVD sweep.

At terminal nodes, use the same 64 literal payoff groups as ADR-0063. Construct
an untruncated TT from the complete Cartesian payoff, then numerically round it
at relative tolerance `1e-13`. Cache identical terminal operators. Public-tree
composition uses tolerance `1e-12` at every strategic node, with optional fixed
rank caps.

No belief enters composition. A policy-conditioned root TT is reusable across
every range with the same board, hand axes, bet tree, and policy.

## Independent dense oracle

Build the identical 385-node public tree from one compatible representative
deal. For each target player, recursively evaluate full Cartesian dense payoff
arrays:

1. return the literal grouped payoff at a terminal;
2. broadcast each hand-dependent action probability on the acting seat axis;
3. sum weighted children; and
4. discard child arrays as recursion returns.

This oracle never materializes a dense joint belief. It is independent of TT
addition/rounding and defines exact root-operator and root-utility labels.

At four hands per seat, additionally materialize the exact compatible belief
and compare the dense root utilities with `PublicTreeTensorEvaluator`. This
checks public histories, information keys, action ordering, policy defaults,
and terminal grouping against the established quotient implementation.

## Frozen workload

Use the fixed river board `2c 7d 9h Js Qc`, pot `12`, stack `30`, bet `3`, and
six seats. Require exactly 385 public nodes, 193 terminals, and 64 terminal
payoff groups.

Cross:

- four and seven hands per seat;
- balanced and blocker-heavy axes;
- one- and three-component exact beliefs;
- uniform, hashed-dense, and hashed-pure policies;
- target seats 0, 3, and 5; and
- node rank caps 8, 16, 32, plus a tolerance-only exact arm.

The three target seats cover the first actor, a middle seat, and the last seat.
The pure policy supplies zero-reach histories; no reach pruning or missing-key
shortcut is allowed.

For each family/size/target, report terminal compile time, deduplicated operator
count, maximum literal terminal error, and terminal ranks. For each policy and
arm, report composition time, maximum raw pre-round rank, root ranks, root TT
bytes, dense bytes, root tensor error, and reconstruction time. For each belief,
also report direct-contraction time, utility error, middle rank, feature work,
and peak numeric bytes.

## Exact arm

The tolerance-only arm has no rank cap. It must simultaneously satisfy:

- maximum terminal-operator error at most `1e-9`;
- maximum dense-root tensor error at most `1e-8`;
- maximum dense-root utility error at most `1e-8`; and
- maximum four-hand quotient utility disagreement at most `1e-10`.

Failure blocks interpretation of every compressed arm.

## Compressed-arm hypothesis

One single declared cap at most 32, without retuning by hand count, family,
policy, target seat, or belief, is value-safe only if it has:

- maximum payoff-span-normalized root utility error at most `1e-4`;
- root TT bytes at most `0.25` of the dense root tensor in every case; and
- middle rank at most `0.25 * (64 * 8) = 128`, the feature-width proxy for 64
  independent rank-8 payoff passes.

Require at least one such arm. Tensor Frobenius error is diagnostic and cannot
override the utility gate. Passing establishes a fixed-policy value primitive,
not strategic safety.

## Timing interpretation

Separate and report:

- terminal payoff TT compilation, cached across policies and beliefs;
- root public-policy composition, cached across beliefs;
- root TT reconstruction for oracle diagnostics; and
- hot direct factor-belief contraction per belief.

Do not combine cached compilation with hot range evaluation or compare Python
composition time with an online latency target. Do compare feature work and
storage with the explicit 64-pass alternative.

## Interpretation branches

- If terminal identity fails, fix numerical TT rounding before public-tree work.
- If the exact root fails, fix action-core multiplication, TT addition, or
  rounding before examining caps.
- If no compressed arm is safe, root policy composition causes rank explosion;
  test shared contender/action structure or a neural residual rather than
  increasing rank without a quality/ms screen.
- If a cap passes, extend contraction to leave the target player's hand mode
  open and reproduce conditional action scores and literal best-response
  actions.
- If pure-policy cases alone fail, do not erase unreachable histories. They are
  required for later off-path safety.

## Dissent protocol

**Confidence:** high in the dense oracle and TT algebra controls; moderate that
one root operator compresses; low that scalar value-safe rank predicts
conditional action-value rank.

**Opposing evidence:** arbitrary hand-dependent policies can make a sum of
terminal low-rank functions full rank. Per-node rounding errors can also align
coherently across 385 nodes.

**Largest risk:** a small root utility error that hides a response-action flip
on a rare blocker hand.

**Cheapest falsification:** any exact-arm root disagreement above `1e-8`, or no
fixed cap at most 32 satisfying utility, storage, and feature-work gates across
all frozen cases.
