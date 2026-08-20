# ADR-0063: Preregister showdown value-operator rank screen

**Status:** Accepted before tensor-train implementation, decomposition, or labels

**Date:** 2026-08-19

## Decision

Test tensor-train compression where signed low rank is mathematically natural:
the six-player showdown payoff operator. Keep the ADR-0062 probability belief
exact as nonnegative unary/mixture factors plus exact card compatibility.

Construct every distinct terminal payoff operator on small full Cartesian hand
axes, decompose it with TT-SVD, reconstruct fixed rank caps, and propagate the
result through the exact public tree. Judge ranks by root utilities, every
unilateral best-response value, and literal response actions. Tensor error is a
diagnostic, never the selection target.

The frozen configuration is
`experiments/configs/showdown-value-operator-rank-screen-v1.json`. The result
target is
`experiments/results/showdown-value-operator-rank-screen-v1.json`.

This is revealed engineering. It can select or reject an operator
representation family for further implementation. It cannot select a poker
strategy, CFR variant, neural model, scheduler, or online deployment rule, and
it cannot access validation or test data.

## Operator separation

For terminal public state `t`, player `p`, and private-hand assignment `h`, let
`U[t,p,h]` be the literal multiway payoff. Define it on the complete Cartesian
hand axes, including assignments where two seats reuse a physical card. The
extension uses each hand's ordinary seven-card rank and the terminal's contender
set. Values on impossible assignments do not alter poker semantics because the
exact compatibility factor remains outside the operator and assigns them zero
weight.

Do **not** decompose `compatibility * U`. ADR-0062 already represents card
compatibility exactly. Multiplying its sparse zero pattern into the payoff
would conflate belief constraints with value-operator rank and would charge TT
for solving the wrong problem.

The six-player one-bet public tree has 193 terminal nodes but only 64 payoff
types:

1. one all-check showdown with no new contributions; and
2. one type for each nonempty contender/caller subset, with every contender
   contributing the fixed bet.

Group terminal nodes by this exact payoff identity. Store TT operators for the
first five players and derive player six as the negative sum, preserving the
game's zero-sum invariant and avoiding redundant storage.

## Frozen workload

Use the fixed board `2c 7d 9h Js Qc`, pot `12`, stacks `30`, and bet `3`.
Generate the same deterministic balanced and blocker-heavy factor-belief hand
axes as ADR-0061.

### Spectral slice

At four and five hands per seat, construct all 64 payoff groups for the first
five players. For each operator, report:

- exact Cartesian Float64 bytes;
- full unfolding singular spectra;
- numerical TT ranks at relative threshold `1e-12`;
- untruncated TT-SVD reconstruction error and storage; and
- reconstruction error and storage at rank caps `1, 2, 4, 8, 16, 32`.

This slice measures rank generalization only. It cannot select a rank using
Frobenius error.

### Root-strategic slice

At four hands per seat, cross both hand-axis families with one- and three-
component exact beliefs and uniform, hashed-dense, and hashed-pure policies.
The behavioral policy schema and card-compatible joint distribution remain
literal.

For each rank cap and the untruncated arm:

1. reconstruct every grouped payoff operator;
2. derive player six by negative summation;
3. gather only the exact compatible deals into terminal value tensors;
4. evaluate the same policy with the exact public-tree quotient semantics;
5. compare utilities, response values, deviation gains, NashConv, and every
   response action with the literal terminal control; and
6. report maximum zero-sum error, operator error, normalized strategic error,
   action mismatches, storage bytes, reconstruction/decomposition time, and
   compression ratio.

The pure policy creates unreachable information sets and retains the legal-
action tie stress. No reach threshold may erase their action maps.

## Frozen exactness gates

The untruncated TT-SVD arm must have:

- maximum payoff-operator error at most `1e-10`;
- maximum root-strategic metric error at most `1e-10`;
- zero literal response-action mismatches; and
- maximum per-deal terminal zero-sum error at most `1e-10`.

Failure stops the branch before interpreting truncated ranks.

## Frozen compressed-arm hypothesis

A compressed arm is strategically safe only if one **single** declared cap at
most 16, without family/policy/component retuning, simultaneously has:

- maximum payoff-normalized strategic error at most `1e-4` across every root
  case;
- zero literal response-action mismatches;
- maximum zero-sum error at most `1e-10`; and
- total grouped TT storage at most `0.25` of the first-five-player dense
  operator bytes.

Require at least one such arm. Rank 32 remains a diagnostic and cannot satisfy
the maximum-safe-rank gate. If the hypothesis fails, do not tune the threshold,
drop the pure arm, or select ranks per family after seeing labels.

## Timing interpretation

This screen reconstructs dense tensors to obtain strategic labels. Report
decomposition, reconstruction, and override-evaluation costs separately, but
make no online speed claim. A rank can advance only to a later direct
factor-network contraction that never reconstructs the Cartesian tensor.

## Branching interpretation

- If the exact arm fails, correct TT or terminal-group semantics first.
- If a compressed arm passes, implement direct contraction of TT payoff cores,
  exact compatibility, and unary/mixture beliefs; benchmark it against cached
  MITM and sampling.
- If no compressed arm passes, generic TT is not the value path on this
  workload. Next test structured winner-summary contraction and a neural
  counterfactual-value model trained with root/action losses.
- Spectral evidence may explain a failure but cannot override root-strategic
  rejection.

## Dissent protocol

**Confidence:** high in exact reconstruction and strategic measurement;
moderate that small-axis TT ranks predict wider ranges; low that independent
per-terminal TT is the best shared representation.

**Opposing evidence:** payoff groups share substantial structure that this
screen does not exploit. A failed independent-TT arm may still motivate a
single conditional operator with contender/action inputs or a neural model.

**Largest risk:** using low Frobenius error to bless a rank that flips a rare
nut-blocker response.

**Cheapest falsification:** any untruncated action mismatch, or no rank at most
16 that achieves both 4x operator storage reduction and literal response-action
identity.
