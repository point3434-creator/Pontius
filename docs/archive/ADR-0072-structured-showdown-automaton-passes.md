# ADR-0072: Exact sparse showdown automaton passes the 32-hand gate

**Status:** Implemented; all twelve frozen gates pass

**Date:** 2026-08-19

## Result and provenance

ADR-0071 replaced dense Cartesian showdown construction with a deterministic
seat-mode automaton whose bond state is the running maximum strength, its
multiplicity, and whether the target seat is in the argmax. Sunk contributions
remain a separate rank-one constant.

The frozen configuration SHA-256 is
`f145fb39f7d41fa81c4f6d0167b72c6e625039a34d706aba544121bf1e9bd7b4`.
The result is
`experiments/results/structured-showdown-automaton-audit-v1.json`, SHA-256
`ecbdee80beb71f229ea478bdc6b4b861f2fdb10db9f17a002c58a7db9437d299`.
It ran from clean commit
`b89b5b1eeb010fb5d4bd0912d4610ce97a447749` in 21.605 seconds. All 386
tests passed in 54.644 seconds before the frozen run. The audited automaton
implementation SHA-256 is
`1a7a142cd446cf36802f1ff19a0189c00229ca5c3f05d0d061374a73dc68f498`.

The workload built 4,608 automata: three hand-axis widths, two range families,
two within-axis orders, 64 terminal groups, and six target seats. Each was
built twice for byte-identical determinism.

## Exactness passes

Every frozen correctness control passes:

- maximum complete four/seven-hand automaton error: exactly `0.0`;
- maximum direct one-hot-TT export error: exactly `0.0`;
- maximum complete four/seven-hand six-seat zero-sum error: exactly `0.0`;
- deterministic transition mismatches: `0`;
- deterministic rebuild mismatches: `0`;
- maximum within-mode permutation spectrum disagreement: `9.828e-14`;
- maximum 32-hand sampled zero-sum residual: `1.776e-15`; and
- no SVD, Cartesian builder allocation, missing group, or missing target.

Zero sum alone could miss a consistent wrong-winner bug. A post-freeze
diagnostic therefore evaluated all six literal showdown payoffs directly on
the same 4,096 assignments for every wide terminal group, without an automaton
or Cartesian tensor. Maximum automaton disagreement is `4.441e-16`. This is an
added diagnostic, not a retroactive frozen gate, but it independently covers
the state-compaction and level-indexing failure class on the 32-hand path.

## Sparse storage passes decisively

One dense `32^6` Float64 payoff operator is 8,589,934,592 bytes. The observed
wide geometry is:

| Family | Maximum state rank | Largest sparse automaton | All 384 automata | First-build time for 384 |
|---|---:|---:|---:|---:|
| balanced | 187 | 97,048 B | 10,393,424 B | 526-534 ms |
| blocker-heavy | 173 | 92,000 B | 9,697,000 B | 499-552 ms |

The largest automaton uses `0.00113%` of one dense operator and is 92.7 times
below the frozen 9 MB ceiling. The largest full 384-automaton set is 49.6 times
below the 512 MB ceiling. A first Python build averages 1.30-1.44 ms per wide
automaton; the slowest observed individual build is 6.90 ms. These are
construction measurements, not native contraction latency.

The maximum hypothetical dense one-hot TT export is 13,143,808 bytes for one
operator, about 135 times the corresponding sparse transition representation.
The ADR-0071 choice to store one `int32` next-state ID per state/hand and demote
one-hot cores to a small-axis oracle is therefore materially validated.

Reachable rank still grows with distinct strength levels. For one balanced
all-contender target the state ranks are
`(1, 26, 64, 105, 145, 184, 1)`; another target reaches the workload maximum
187. Compactness comes from deterministic sparse transitions, not low ordinary
TT rank.

## Sorting is a locality control, not a rank result

There are zero strength-sorted run-count violations and the singular-spectrum
invariant passes. Balanced axes receive no run reduction because their
stratified generator is already monotone in strength. On the 32-hand blocker
family, sorting reduces transition runs from 302,018 to 262,522 (`13.08%`) and
terminal-output runs from 41,626 to 29,526 (`29.07%`). It does not reduce raw
`int32` storage and does not reliably reduce Python build time. The evidence
supports optional run encoding or locality, not a TT compression or latency
claim.

## Structural sharing is real but byte-light at width 32

Each geometry contains 384 logical group/target objects but only 378 distinct
`(contender set, target)` pairs because all-check and the full contributed set
share a contender set. Collapsing every outside-contender target to one zero
winner shortcut leaves 193 executable winner topologies: 192 nonzero
`(set, target-in-set)` forms plus one zero form.

Despite that nearly twofold logical reuse, projected normalized-winner sharing
reduces 32-hand numeric bytes by only about 6.9%: 10.39 to 9.69 MB on balanced
axes and 9.70 to 9.03 MB on blocker-heavy axes. Distinct active-target tables
hold most bytes. Share the topology because it is exact and useful downstream,
but do not treat it as the main wide-storage mechanism.

## Scope boundary

The terminal closure `pot / winner multiplicity` is exact for this equal-stack,
single-bet river tree, which has no side pots. Unequal effective stacks or
all-ins require contribution classes and side-pot eligibility in the bond
state. This audit also covers 32 selected hands per seat, not all 1,081 legal
river hole-card combinations for a board.

The result removes dense terminal construction as the frozen 32-hand blocker.
It does not show that an arbitrary fixed public policy has compressible root
values, expose conditional action values, certify best responses, or establish
online decision latency.

## Decision

Adopt the sparse deterministic automaton as the exact terminal source for the
next 32-hand representation audit. Reject dense Cartesian payoff construction
and dense one-hot TT cores as production terminal formats.

The successor now measures the actual customer:

1. real DCFR-average and literal-best-response policy provenance, alongside
   uniform and hash controls;
2. crown ranks and seat-cut behavior;
3. fixed-belief whole-seat policy candidates;
4. clean-fringe, no-rounding scalar reads versus both recompose-then-contract
   and the flat/enumerated evaluator incumbents; and
5. deterministic below/inside/above-guard cases, with explicit abstention.

No small-axis speed win can authorize a 32-hand path. The successor must report
frontier size, delta-support frontier, frontier-rank histogram, total contraction
feature width, cost-weighted dirty closure, and batched bill so scaling can be
attributed rather than inferred.

## Dissent protocol

**Confidence:** very high in automaton identity and 32-hand sparse storage;
high in Python construction viability; low in downstream policy compression.

**Opposing evidence:** maximum reachable state rank already reaches 187 at 32
hands, and arbitrary public policies previously produced crown ranks above 200
at only seven hands.

**Largest risk:** promoting an exact terminal representation into a claim about
root policy values or full-deck NLHE before the policy and action axes pass.

**Cheapest falsification:** a real DCFR-average policy whose frontier/crown
geometry makes both no-rounding reads and explicit public-state contraction
more expensive than the enumerated small-axis controls with no credible scaling
path.
