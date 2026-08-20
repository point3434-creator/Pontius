# ADR-0081: Preregister open-mode factor-TT and quotient-CFR bridge audit

**Status:** Accepted after reduced algebra/solver controls and a disclosed wide
terminal engineering screen, but before any canonical checkpoint-16 infoset
result

**Date:** 2026-08-20

## Decision

Run one additive audit of the conditional primitive required by ADR-0080. The
frozen configuration is
`experiments/configs/open-mode-factor-tt-audit-v1.json`; its SHA-256 is
`9bd81772c1166a62ef2cfc965fb5dbce1a3b72b78f73b916c4d0deb84ff1a99f`.
The result target is
`experiments/results/open-mode-factor-tt-audit-v1.json`.

The audit has two deliberately separate products:

1. an exact small-axis bridge from cached public-child TTs to every
   `PublicTreeTensorCFR` action table at four and seven hands; and
2. a dense-free 32-hand structural path from int32 showdown transitions to
   conditional hand vectors and a two-action comparison.

Passing the first establishes solver semantics. Passing the second establishes
representation and memory, not online latency. Neither establishes that a
full 32-hand CFR iteration is affordable.

## Open-mode identity

For compatible private assignment `x`, factor-belief unnormalized mass
`w(x)`, common nonnegative public-reach unary factors `r_i(x_i)`, and value
operator `V(x)`, leave target hand `h` open:

`D_t(h) = sum_{x: x_t=h} w(x) product_i r_i(x_i)`

`N_t(h) = sum_{x: x_t=h} w(x) product_i r_i(x_i) V(x)`.

The root-normalized reach and numerator divide by the original belief
partition. The conditional value is `N_t(h) / D_t(h)` only for positive reach.
Zero reach has an explicit finite fallback and a false reach mask.

The card topology remains split 3/3. Every complete assignment on one query
half already contains the scalar contribution for all three private-hand axes
on that half. Grouping records by each hand index therefore produces all three
open vectors after one directional incidence pass. All six target axes require
two directions, not six independent contractions.

Several public children share a denominator. Their middle ranks are sliced and
packed under a fixed feature-width ceiling; every slice contributes to its
child's per-record numerator before hand grouping. This is primarily a bounded
memory and shared-reach form. The pre-freeze screen does not support claiming
that concatenating child features is faster than separate child calls.

## Exact quotient-CFR bridge

At a public node owned by traverser `t`, reconstruct counterfactual public
reach above the node as unary hand factors. Multiply every ancestor action
probability except actions taken by `t`; repeated actions by one opponent
multiply on the same private-hand axis. For each legal child action, the cached
child TT contains the complete fixed-policy continuation below that action.

The open-mode root-normalized numerator is then exactly the action score used
inside `PublicTreeTensorCFR`:

`S_a(h) = sum_{deal: hand_t=h} counterfactual_reach(deal) V_child_a(deal)`.

The policy value is `sum_a pi_t(a|h) S_a(h)` and the instantaneous regret
delta is `S_a(h) - policy_value(h)`. The audit uses checkpoint-16 DCFR average
policies from the immutable source artifact at both hand counts and both range
families. It checks all 192 strategic public nodes per geometry: 768 infoset
rows total.

Require, over every hand/action entry:

- reach error at most `1e-10`;
- action-numerator error at most `1e-8`;
- positive-reach conditional-value error at most `1e-8`;
- regret-delta error at most `1e-8`; and
- exact selected-action identity.

One four-hand balanced control also compares the literal trace with the actual
regret changes applied to player zero by a production quotient-CFR step. Its
maximum error must be at most `1e-10`. This triangulates the new reader, a
literal deal-axis trace, and the existing solver rather than merely comparing
two new formulations.

## Zero-reach semantics are an action gate

On the four-hand balanced control, set the root's first action probability to
zero for every root hand and choose a later information set below that branch.
At every completely unreachable target infoset:

- select the first legal action exactly, matching NumPy's stable `argmax`
  convention in the literal evaluator;
- return an explicit false positive-reach mask; and
- apply bitwise-zero regret change.

At least one zero-reach row is required. A small error norm cannot substitute
for action and accumulator identity. This prevents a division convention from
silently changing off-path safe-resolving behavior.

## Direct structured-terminal path

The 32-hand arm must not call `StructuredShowdownAutomaton.to_dense()` and must
not promote `to_tensor_train()`'s one-hot dense cores into the production path.
It consumes the frozen int32 transitions directly.

At the 3/3 split, a left partial assignment reaches one deterministic middle
state. Its left vector is therefore one-hot. For every right partial assignment,
replay transitions from every possible middle state and read the final winner
share. Append one rank-one coordinate for the sunk contribution. This creates
only two-dimensional assignment-by-state half vectors; it never creates a
`32^6` payoff tensor.

For both balanced and blocker-heavy 32-hand geometries:

- compare the factor workspace partition and all six open reach marginals to
  the independent meet-in-the-middle belief contraction;
- directly contract all six all-check showdown automata and require root
  zero-sum error at most `1e-9`;
- contract a constant losing shortcut and require every conditional value to
  match its sunk payoff within `1e-10`;
- produce finite legal choices from a two-automaton action batch;
- keep sparse automata below 2 MB total;
- keep estimated peak numeric storage below 1 GB and below 12.5% of one
  8.59 GB dense Float64 operator; and
- declare that neither a Cartesian payoff nor a one-hot TT export was built.

Wide timing is mandatory telemetry but is not a pass gate. The structural arm
cannot be called online-ready regardless of whether it passes memory and
identity.

## Pre-freeze engineering disclosure

The following was observed before this freeze and therefore is engineering
evidence, not a held-out result:

- reduced four-player literal assignments matched all open reaches,
  numerators, conditional values, and weighted scalar contractions within
  about `3e-14`;
- a two-child forced rank-sliced batch reproduced independent literal vectors;
- a three-player bridge matched both a literal CFR trace and the actual
  quotient solver's regret update, including exact zero-reach action and regret
  behavior;
- direct sparse automaton half vectors matched the diagnostic one-hot TT export
  on reduced axes;
- synthetic rank-8 h32 all-six open contraction took about 0.58 seconds in
  NumPy; grouping three target axes cost about one-third of three independent
  calls, while two-child batching was approximately neutral at mature ranks;
- on noncanonical wide engineering axes, six direct all-check automata required
  about 13.6-15.9 seconds, 180-212 MB of half vectors, and a 602-712 MB estimated
  peak; sparse automata themselves occupied only about 0.47-0.51 MB; and
- the same automata's unused one-hot TT exports would occupy roughly 50-58 MB.

These observations set the 1 GB structural ceiling and explicitly falsify any
millisecond interpretation in advance. No canonical checkpoint-16 h4/h7
infoset error, selected action, rank, timing, or action-gap result was observed
before freezing.

The complete pre-freeze targeted suite contains seven passing tests. A full
repository regression is required before execution.

## Interpretation branches

- Any reach or numerator failure rejects the incidence direction or CFR reach
  factorization before timing is interpreted.
- Any selected-action failure rejects use for CFR or best response even if all
  value tolerances pass.
- Any zero-reach failure rejects the solver bridge until the semantic
  convention is made identical.
- A small-axis pass plus wide memory failure sends the representation back to
  sparse state/incidence fusion; it does not authorize more RAM.
- A complete pass authorizes implementing one full dense-free quotient-CFR
  iteration and matching its h4/h7 trajectory before attempting genuine
  32-hand checkpoints.
- Even after a complete pass, the observed seconds-scale wide terminal bill
  makes a fused/native kernel or a more strongly factorized state contraction
  necessary before online use.

## Dissent protocol

**Confidence:** high in the open-mode and CFR algebra; high in reduced action
semantics; moderate in checkpoint-16 action identity under rounded child TTs;
high that 32-hand storage passes; low that the Python wide path is economically
useful.

**Opposing evidence:** real average-policy child TTs are near-generic, the wide
direct automaton screen is already seconds-scale, and assignment-by-state half
vectors partially re-densify the sparse automaton even though they avoid the
Cartesian tensor.

**Largest risk:** celebrating a dense-free structural pass while ignoring that
one CFR iteration must repeat conditional action reads across 192 strategic
nodes and continually rebuild policy-conditioned continuations.

**Cheapest falsification:** one canonical selected-action mismatch rejects the
solver bridge. Otherwise, a wide peak above 1 GB rejects the direct half-vector
form. Passing both still leaves the measured full-iteration bill as the next
mandatory falsification, not an assumed success.
