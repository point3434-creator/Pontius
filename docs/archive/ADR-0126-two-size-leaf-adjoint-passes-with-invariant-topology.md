# ADR-0126: Two-size leaf adjoints pass with invariant transition topology

## Status

ADR-0125 executed from its clean preregistration commit and every frozen gate
passed.

## Evidence

The 50,353-byte result artifact is
`experiments/results/multi-size-leaf-adjoint-audit-v1.json`, SHA-256
`5036ad696e0e26dedbcb709ef5d1b73b317afc5585c5f7d8b52a36088ff7ac50`.
Its configuration SHA-256 is
`6560c8a42b991c4eddcb892f54612001556efd38db926e18c2eeaa2ad1227d45`.
The artifact records a clean Git state at
`8021e3a7fa0fd819cc742c0d4f828a21c0424c6f`.

The four cases contained 727 and 549 compatible h4 deals, then 26,978 and
18,768 compatible h7 deals for the balanced and blocker-heavy families.  The
complete run took `12.0451 s`, including exact dense teachers, 3,048 terminal
automata across both widths, resident-cache construction, and all leaf reads.

## Exactness result

All 19 frozen gates passed.

- Every terminal transition replay matched: zero mismatches.
- Every automaton payoff matched its contribution-aware dense terminal value
  exactly: maximum error zero.
- Every dense terminal tensor was exactly zero sum.
- All 1,512 leaf-adjoint action reads were present across 24 traversers.
- Maximum counterfactual-reach error was `5.274e-16`.
- Maximum action-numerator error was `3.997e-15`.
- Maximum conditional-action-value error was `2.451e-13`.
- Maximum regret-delta error was `3.331e-15`.
- Maximum child-reach disagreement was `5.551e-17`.
- There were zero raw action-index mismatches and exactly zero teacher-measured
  action-value loss.

The bridge therefore preserves the actual CFR quantities, not merely root
utility or terminal conservation.  The sized action history, contribution
groups, factorized belief, dense teacher, and GPU leaf contraction agree at
Float64 noise.

## Public-tree cost

The measured shape equals the preregistration:

| Quantity | One size | Two sizes | Ratio |
|---|---:|---:|---:|
| Public nodes | 385 | 763 | 1.982x |
| Strategic nodes | 192 | 378 | 1.969x |
| Terminal nodes | 193 | 385 | 1.995x |
| Terminal payoff groups | 64 | 127 | 1.984x |
| Policy entries, h4 | 1,536 | 3,048 | 1.984x |
| Policy entries, h7 | 2,688 | 5,334 | 1.984x |

This is controlled duplication, not an unexpected branching explosion.  The
extra size nearly doubles the no-raise public contract because every potential
bettor receives one extra response tree.

## The important structural result

Action width did not increase automaton state complexity.

| Case | One-size max rank | Two-size max rank | Distinct transition topologies, each |
|---|---:|---:|---:|
| h4 balanced | 20 | 20 | 378 |
| h4 blocker-heavy | 16 | 16 | 378 |
| h7 balanced | 38 | 38 | 378 |
| h7 blocker-heavy | 36 | 36 | 378 |

The one-size library has 384 seat/group automata and the two-size library has
762, yet both have exactly 378 distinct transition topologies.  Six apparent
one-size duplicates arise because all-check and all-call share the same full
contender set for each target.  Adding a second amount creates new payoff
scalings and public reaches, but no new showdown state machine.

The current object representation does not exploit that fact.  Raw automaton
bytes grow `1.954x` to `1.960x`; resident half-vector cache bytes grow `1.955x`
to `1.961x`; total resident middle rank grows by the same factor.  Maximum rank
is unchanged.  Thus the present cache duplicates amount-specific numeric
payloads even though its transitions are structurally identical.

The terminal payoff for fixed contenders and target is affine in bet amount:
the final pot is `P + |S|b`, and the target's sunk contribution is either `b`
or zero.  A future cache can separate the shared winner/topology basis from the
amount coefficient.  This is an evidence-backed representation opportunity,
not authorization to assume the contraction bill disappears: the two public
branches retain different policy reaches and still require separate leaf
terms.

## Memory and timing boundaries

The largest exact h7 case used approximately `499 MB` of persistent layout
arrays and `1.153 GB` of estimated hot scratch, or `1.652 GB` combined.  Peak
GPU-pool allocation was `96.2 MB`.  Both are far below their frozen ceilings.

Leaf timing is diagnostic only.  The first invocation of a new GPU direction
or shape paid compilation overhead, including one `2.758 s` h7 balanced
outlier; subsequent h7 leaf traversers were approximately `98–149 ms`.  Dense
h7 traversers were approximately `100–194 ms`.  No online speed conclusion is
licensed because the audit intentionally constructs dense teachers and cold
Python/CuPy paths.

## Decision

Accept the sized six-seat game, contribution-aware terminal groups, tensor
teacher, and leaf-adjoint traverser as exact controls.

The next experiment is an h32 preflight, not a strategy claim.  On the same
frozen h32 beliefs used by the resident lineage, compile one-size and two-size
resident terminal caches and report exact persistent bytes, pool headroom,
middle-rank width, and cold construction bill.  If the current two-size cache
fits with safe scratch headroom, continue in that same preregistration to one
resident warm step and compare its marginal bill with the one-size incumbent.
If it does not fit, stop before a step and build the affine/shared-topology cache
rather than tuning allocation order.

Do not yet train a two-size blueprint or infer that the added action improves
strategy.  Correctness and representation geometry are now established;
strategy quality per millisecond remains unmeasured.

## Scope

This result covers one board, equal stacks, two opening sizes, one river betting
round, no raises, no all-ins, and reduced hand axes.  It does not cover side
pots, earlier streets, a full 1,081-combo river range, or production latency.
