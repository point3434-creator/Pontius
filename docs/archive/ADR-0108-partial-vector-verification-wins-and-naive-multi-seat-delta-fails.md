# ADR-0108: Partial-vector verification wins and naive multi-seat delta fails

**Status:** Acceptance-aware partial-vector verification accepted for h32
fixed-envelope candidate portfolios; exact ordered-seat terminal delta rejected
for whole-profile candidates

**Date:** 2026-08-20

## Result

The sealed ADR-0107 audit completed from clean commit `0981c0f` with every
frozen gate passing. The canonical local artifact is
`experiments/results/h32-policy-delta-verifier-audit-v1.json`:

- SHA-256:
  `2fb53315812ee2afeb2d3d50399770140c1fcd0e4bb29e4d6cc54ca19743a489`;
- size: 543,649 bytes;
- config SHA-256:
  `ea0cd0840de3a2fc31114963ae45dd8b3d3ca6a4906fdaff585a78001d79bb4b`;
- audit implementation SHA-256:
  `16a5e7cad3146a513715dec18376fd86da080c0e915fd07a1b2f79485d15ccfd`;
  and
- verifier implementation SHA-256:
  `db8040b0a94cc9ffe95fb4b8854a1924525a63093464cb5523f897763a45a053`.

Total audit wall time was 610.876 seconds. It reconstructed 52 frozen h32
policies, performed 133 live exact seat reads, and created zero new
strategy-quality labels.

## Correctness result

The partial verifier returned the exact ADR-0106 policy digest on every target.
The canonical stream and all 67 frozen candidate arrival orders agreed. Every
live stop occurred at the same seat and for the same reason as the frozen
six-seat teacher simulation.

The numerical controls passed with substantial margin:

| Quantity | Maximum measured error or use | Gate |
|---|---:|---:|
| Seat utility error | `5.05e-15` | `1e-9` |
| Seat best-response error | `5.13e-15` | `1e-9` |
| Seat deviation-gain error | `1.39e-15` | `1e-9` |
| Completed NashConv error | `2.55e-15` | `1e-9` |
| Completed zero-sum residual | `7.54e-15` | `1e-9` |
| Maximum seat-read time | 6.402 s | 60 s |
| Maximum host numeric peak | 1.487 GB | 3 GB |
| Maximum GPU pool | 2.127 GB | 4 GB |

All source hashes, target descriptors, candidate unions, policy digests, and
the accepted CUDA geometry reproduced. Same-day complete-candidate calibration
ratios ranged from `0.9883` to `1.0007`, so the historical full-profile bills
were stable enough for the frozen comparison.

## Economics result

The verifier evaluated 133 of the 312 seats required by indiscriminate
six-seat evaluation. The structural reduction was `2.346x`; measured,
drift-calibrated portfolio speedup was `2.171x`.

| Range family | Belief shift | Seat reads | Completed candidates | Partial bill | Calibrated full bill | Speedup |
|---|---|---:|---:|---:|---:|---:|
| balanced | local blocker | 49 / 78 | 6 | 247.3 s | 373.0 s | `1.508x` |
| balanced | all-seat strength | 20 / 78 | 1 | 107.1 s | 368.8 s | `3.443x` |
| blocker-heavy | local blocker | 46 / 78 | 5 | 171.5 s | 276.1 s | `1.610x` |
| blocker-heavy | all-seat strength | 18 / 78 | 1 | 71.3 s | 278.4 s | `3.906x` |

Pooled live bill was 597.195 seconds against a calibrated full bill of
1,296.347 seconds. Both family gates passed: balanced at `2.093x` and
blocker-heavy at `2.284x`.

This is a portfolio result, not a cheaper proof for a winning candidate. The
balanced and blocker-heavy local winners still required all six exact seat
values. Savings came from refusing to finish candidates that had already
violated one blueprint cap.

## What actually stopped work

All 39 incomplete candidate reads stopped on a literal blueprint-cap breach:

- 31 stopped at seat zero; and
- eight stopped at seat two.

Thirteen candidates completed. No candidate stopped on the objective
lower-bound rule. Accordingly, all 67 candidate arrival orders used the same
seat count on each target: 49, 20, 46, and 18 respectively. The audit proves
the objective-bound implementation through frozen synthetic controls, but the
h32 corpus supplies no live economic evidence for that branch.

The dense shifts were especially cheap because 23 of their 24 rejected
candidates failed at seat zero. This is useful behavior, but it is also the
largest transfer risk: a new board, tree, or candidate generator can move the
first cap violation later in the vector.

The fixed seat order `0,1,2,3,4,5` therefore remains a declared, label-free
baseline—not an empirically optimal scheduler. We will not fit a seat selector
to these four targets.

## Exact policy-delta result

The optimistic exact delta screen rejects the proposed whole-profile terminal
delta path before native implementation.

Search average one has a distinct serialized digest but is behaviorally equal
to the blueprint to at most `2.22e-16`; it correctly has zero support under the
frozen `1e-15` delta tolerance on all four targets. Every one of the other 48
target/candidate rows:

- changes all six seats;
- changes all 192 public decision nodes;
- supports 5,790 ordered-seat terminal delta terms; and
- requires one signed value term for each of the five changed opponent seats
  per response target.

The resulting profile widths were:

| Range family | Existing value-plus-mass width | Optimistic delta value width | Ratio |
|---|---:|---:|---:|
| balanced | 121,674 | 591,000 | about `4.86x` |
| blocker-heavy | 93,876 | 452,010 | about `4.82x` |

Across all 52 rows, the median optimistic ratio was `4.815`; only the four
identity rows were narrower. The baseline terminal-numerator cache would have
cost only 296,448 bytes per target, but cheap storage cannot rescue fivefold
contraction width.

This is the exact distinction ADR-0107 was designed to expose. A local edit can
be an excellent policy-delta customer—the h4 one-node control measured about
`0.014x` full width—while a whole-profile CFR checkpoint is the wrong customer.
“Delta” describes the algebra, not its economics.

## Bottleneck localization

Of the 597.195-second live verifier bill:

- terminal contraction consumed 593.276 seconds, or 99.34%;
- candidate probability compilation consumed 2.030 seconds;
- reverse evaluation consumed 1.029 seconds; and
- the remaining orchestration was below one second.

The next systems optimization therefore has a measured customer and a nearly
complete attribution. It is not another Python stopping rule or a generic
multi-seat delta. It is the h32 terminal contraction path: resident feature
construction, fused folding/contraction, and candidate/seat batching where the
same compiled card topology can be reused.

Any such audit must still compare against the accepted partial verifier, not
against indiscriminate full-vector evaluation. It must preserve cap-stop
semantics and charge probability compilation, transfers, synchronization, and
all resident setup symmetrically.

## Decision

1. Adopt acceptance-aware partial-vector verification as the exact h32
   fixed-envelope portfolio evaluator.
2. Preserve fixed blueprint caps and the canonical set-valued final selector;
   early stopping may omit proofs for rejected candidates but may never change
   the selected digest.
3. Keep full six-seat verification mandatory for every candidate that can
   still enter the envelope optimum.
4. Reject the ordered-seat terminal policy-delta contraction for whole-profile
   CFR checkpoints and interpolations. Do not implement a native kernel for a
   representation already measured at about `4.8x` incumbent width.
5. Retain policy delta as a scoped representation for declared local or
   single-seat edits, where changed support can genuinely be small.
6. Do not install a learned seat or candidate scheduler from this corpus.
   Transfer evidence must precede any label-derived ordering policy.
7. Direct the next performance audit at the terminal contraction path, using
   the accepted partial verifier as the incumbent and retaining a fresh-board
   or wider-tree transfer arm before production claims.

## What this establishes—and what it does not

This result establishes an exact `2.171x` measured reduction in the cost of
verifying the frozen 13-candidate h32 portfolios. It also establishes a clean
negative: the most direct exact multi-seat terminal delta is structurally
worse for every nontrivial candidate in this corpus.

It does not establish a sub-millisecond online solver, a cheap certificate for
an isolated good candidate, coalition safety, transfer to another board, or
economics on a deeper/multi-size betting tree. The result accelerates the
evaluation of already generated policies; it creates no strategy improvement
by itself.

## Dissent protocol

**Confidence:** extremely high in exactness and the negative delta-width
result; high in the measured portfolio economics on this artifact; moderate in
transfer to other h32 river workloads.

**Opposing evidence:** local targets complete five or six candidates and barely
clear the `1.5x` target-level boundary. A generator that emits one strong
candidate obtains essentially no early-stop benefit.

**Largest risk:** the apparent scheduler opportunity is an artifact of dense
shift failures concentrating at seat zero. Fitting that pattern would repeat
the project's rejected selector lineage.

**Cheapest falsification:** replay the same fixed-envelope verifier on a new
river board with a freshly generated candidate stream. One exactness mismatch
rejects the mechanism; a family speedup below `1.5x` rejects transfer of the
economic claim while leaving the stopping proof intact.
