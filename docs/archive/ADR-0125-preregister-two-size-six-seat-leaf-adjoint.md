# ADR-0125: Preregister the two-size six-seat leaf-adjoint bridge

## Status

Frozen after implementation-only h2 controls and before any h4 or h7 sized
leaf-adjoint label or timing.

## Context

ADR-0124 authorized device-resident warm search through iteration eight and
named correctness-scale action widening as the next experiment.  The existing
six-seat game, terminal grouping, and leaf-adjoint solver all deliberately
encode one scalar bet.  Reusing their 64 payoff groups for two bet sizes would
erase contributions and can return numerically plausible but wrong values.

The additive implementation therefore introduces a six-seat sized game, a
contribution-aware public-tree layout, and terminal keys over
`(contenders, bet amount)`.  Development controls used only two hands per seat.
They established betting order, direct terminal payoffs, the expected topology,
and one leaf-adjoint traverser against its dense oracle.  Those labels do not
authorize h4, h7, or h32.

## Frozen workload

Use six equal `30`-chip stacks, a `12`-chip pot, and opening bets of `3` and
`6` chips.  Every unopened seat may check or choose either size.  After a bet,
all other seats fold or call once in cyclic order.  There are no raises,
all-ins, side pots, or unmatched calls.

Run balanced and blocker-heavy beliefs at four and seven hands per seat on the
canonical river board.  Each belief has three mixture components.  Materialize
its exact compatible deal distribution only for the dense teacher; the
leaf-adjoint arm consumes the factorized belief directly.

The public shape is fixed before execution:

- one size: 385 public nodes, 192 strategic nodes, 193 terminal nodes, and 64
  payoff groups;
- two sizes: 763 public nodes, 378 strategic nodes, 385 terminal nodes, and 127
  payoff groups.

The 127 groups are all-check plus one copy of every nonempty contender set for
each bet size.  Any different count is a semantic failure, not an economics
result.

## Exactness gates

For every case and all six target seats:

1. replay every automaton transition independently;
2. compare every supported assignment payoff with the contribution-aware dense
   terminal tensor;
3. require terminal zero sum;
4. compare all 1,512 per-information-set leaf-adjoint action reads with the
   dense deal-axis CFR teacher; and
5. gate reaches, action numerators, conditional values, and regret deltas at
   their frozen Float64 tolerances.

Raw argmax mismatches remain diagnostic because exact ties can select different
indices under different reduction orders.  The binding strategy gate is that
the leaf-selected action loses at most `1e-9` in the dense teacher's own action
numerators.  This preserves the exact-tie lesson from the CSR lineage without
weakening value correctness.

The h7 dense teacher is intentionally expensive.  Host numeric memory is capped
at 8 GB and the GPU pool at 12 GB.  Sixty-four deterministic supported deals
are replayed for topology identity in every case; private cards cannot affect
the legal tree, while sampling avoids pretending a 90-million-state replay is
useful evidence.

## Geometry report

Report, but do not quality-gate:

- public nodes and policy-probability entries;
- automaton records, state ranks, raw bytes, and distinct transition
  topologies;
- resident per-seat half-vector cache bytes and total middle rank;
- dense-teacher and leaf-adjoint wall times; and
- the two-size/one-size ratio for every comparable bill.

These timings include Python orchestration and are not latency claims.  Their
purpose is to reveal whether action width scales through duplicated terminal
groups, higher ranks, larger per-group work, or all three before any native
kernel is widened.

## Decision rule

A pass authorizes a separately preregistered h32 two-size bridge and resident
cache economics screen.  It does not authorize a two-size production action
abstraction, claim that the second size improves strategy, or justify native
optimization.

Any terminal or action-table failure blocks widening and returns to the sized
payoff/grouping boundary.  A memory failure rejects the dense h7 teacher only;
it does not falsify the factorized representation.  Geometry near 2x is an
honest cost result, not a failure, because strategic value has not yet entered
this audit.

## Dissent

**Confidence:** high in the no-raise betting contract and terminal algebra;
moderate that the leaf-adjoint bill will scale near the group-count ratio; low
that a second river size earns that cost in strategy quality.

**Opposing evidence:** heads-up ADR-0038 found roughly 2.7x absolute work for a
3x2 action tree and explicitly withheld a quality claim.  Six-seat terminal
groups may duplicate more cleanly than public nodes but still make h32 resident
caches uneconomic.

**Largest unknown:** whether one extra size changes terminal rank or only the
number of copies.  If rank is invariant and transition topologies pair exactly,
structural sharing may make the h32 lift much cheaper than raw automaton bytes
suggest.

**Cheapest falsification:** the frozen h4/h7 action-table comparison.  Any
non-tie action loss above tolerance kills the bridge before an h32 allocation.
