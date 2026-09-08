# ADR-0071: Preregister exact dense-free showdown automaton audit

**Status:** Accepted before implementation, structured ranks, storage, or timing

**Date:** 2026-08-19

## Decision

Remove the known 32-hand terminal-construction blocker before another root
policy representation screen. Build every six-player river terminal payoff as
an exact deterministic weighted automaton over seat hand modes, without TT-SVD
or a dense Cartesian intermediate.

The frozen configuration is
`experiments/configs/structured-showdown-automaton-audit-v1.json`. The result
target is
`experiments/results/structured-showdown-automaton-audit-v1.json`.

This is a representation correctness and storage audit. It does not select a
root TT cap, certify a policy delta, or establish online latency.

## Exact state machine

For one terminal contender set and one target player, process the six seat
modes in original seat order. After each processed seat, the bond state is one
of:

- an empty sentinel if no contender has appeared; or
- `(running maximum strength, multiplicity, target in argmax)`.

At a noncontender seat, every hand leaves the state unchanged. At a contender:

- a higher strength replaces the maximum, sets multiplicity one, and sets the
  target bit exactly when this seat is the target;
- an equal strength increments multiplicity and ORs the target bit; and
- a lower strength leaves the state unchanged.

After the last seat, output `target_in_argmax / multiplicity`. Multiply by the
terminal final pot. Represent the target's sunk pot share and any called bet as
a separate exact rank-one constant tensor, then sum the two signed terms.
Targets outside the contender set have a zero winner term and only rank-one
sunk value.

State identifiers are local to each bond and assigned by a deterministic sort.
Every `(previous_state, hand)` has exactly one next state. Store only that
`int32` identifier; do not allocate a dense one-hot
`previous_rank x hands x next_rank` core in the production representation.
The last-mode output is Float64.

## Sparse TT semantics

The transition tables are a sparse deterministic TT. They scale with
`previous_rank * hands`, not `previous_rank * hands * next_rank`. For the
four- and seven-hand controls only, export ordinary one-hot TT cores directly
from those transitions and compare them with the literal dense payoff. The
export may not call SVD, rounding, or first materialize the Cartesian tensor.

The 32-hand builder must expose its allocated arrays so the audit can enforce
that every construction array is at most two-dimensional and no allocation has
Cartesian size. Dense reconstruction and dense TT export are prohibited on the
wide arm.

## Frozen workload

Use the same board, pot, stack, one-bet public tree, balanced/blocker-heavy hand
axis generators, all 64 payoff groups, and all six target players as the recent
TT audits.

At four and seven hands:

1. compare every automaton value with `_payoff_operator` on the complete
   Cartesian tensor;
2. export direct one-hot TT cores and compare their reconstruction;
3. sum all six target tensors and require zero sum pointwise; and
4. rebuild each automaton and require byte-identical transitions, state tables,
   and output weights.

At 32 hands, build all group/player automata and evaluate 4,096 deterministic
assignments without constructing `32^6`. Require sampled six-player zero sum
and report construction time, sparse bytes, state counts, transition records,
and the bytes that dense one-hot TT cores would have required.

## Strength-order invariant and locality

Build both the generated axes and a stable within-seat ordering by
`(strength, hole cards)`. On the six frozen representative group/player cases,
compare singular spectra of the complete four/seven-hand tensors after the
corresponding mode permutation. Relative disagreement may not exceed `1e-12`.

This is an invariant control, not a compression hypothesis. Independent
within-mode permutations left/right multiply every unfolding by permutation
matrices, so ordinary TT ranks and singular tails cannot improve.

For the sparse automaton, report transition run count: the number of contiguous
next-state runs across hands for each previous state. Strength sorting must not
increase total runs. It can therefore serve monotone transition compression or
cache locality even though it cannot change TT-SVD rank.

## Frozen storage gates

One `32^6` Float64 operator is 8,589,934,592 bytes. Require:

- at most 9,000,000 sparse numeric bytes for any one wide automaton; and
- at most 536,870,912 bytes summed over all 384 group/player automata.

The first is approximately 0.105% of one dense operator. The aggregate ceiling
is deliberately conservative: it rejects a state-machine explosion while
remaining below one percent of the 64 GB development host.

## Exact gates

Require:

- maximum dense automaton error at most `1e-12`;
- maximum direct-TT-export error at most `1e-12`;
- maximum dense and wide-sampled zero-sum error at most `1e-12`;
- zero deterministic transition mismatches;
- no SVD or Cartesian allocation in construction;
- strength-sorted run count never above generated-order count;
- every group and target present; and
- byte-identical deterministic rebuilds.

Storage failure rejects the automaton as the wide terminal representation even
if small exactness passes. Small exactness failure blocks all successor work.

## Next decision

If the automaton passes, use it as the terminal source for the real-policy
representation screen. That successor must include DCFR average checkpoints,
literal best-response policies, crown ranks, cost-weighted dirty closures,
near-guard abstention controls, and a head-to-head comparison of:

1. recompose, round, then contract; and
2. no-rounding clean-fringe scalar contraction with rounding only after an
   accepted baseline write.

Do not assume the second wins: naive fringe enumeration may replace one crown
SVD with too many factor-TT contractions.

## Dissent protocol

**Confidence:** very high in the state-machine identity; high in small dense
falsifiability; moderate in sparse 32-hand storage; low in downstream public-
policy compression.

**Opposing evidence:** exact reachable-state ranks may grow with the number of
distinct strengths, and a dense-core TT export can still be impractical even
when sparse transitions are compact.

**Largest risk:** calling sparse terminal construction a root value solution
when arbitrary hand-dependent public policies remain the observed rank source.

**Cheapest falsification:** one four-hand contender/target tensor that disagrees
with the literal payoff, or one 32-hand automaton exceeding the frozen sparse
storage ceiling.
