# ADR-0109: Preregister device-resident h32 partial verifier

**Status:** Preregistered; implementation, workload, cache charge, incumbent,
and gates frozen before any h32 resident-contraction timing

**Date:** 2026-08-20

## Decision

Run one post-label systems audit of a device-resident terminal-contraction path
inside the exact ADR-0108 partial-vector verifier.

The customer is fixed and narrow: the same four h32 targets, same 13-policy
portfolios, same 133 exact seat prefixes, and same fixed blueprint-envelope
selection already accepted by ADR-0108. The resident path must produce the
same stop seat, complete-candidate set, and final selected policy digest.

The incumbent is ADR-0108's partial verifier—not indiscriminate six-seat
evaluation and not the rejected ordered-seat delta representation. A system
that wins only against an obsolete baseline fails this audit.

This experiment creates no new policy or strategy-quality label. Its new
evidence is exactness, residency economics, transfer traffic, resource use,
and a small fresh-board mechanism control.

## Mechanism

The accepted CuPy path currently repeats the following sequence for every
feature batch:

1. construct weighted value or mass features on the CPU;
2. concatenate them into a host matrix;
3. transfer the matrix to the GPU;
4. apply the two fixed sparse incidence operators;
5. transfer the complete compatible-feature matrix back to the CPU; and
6. fold it into per-terminal numerator or reach records on the CPU.

ADR-0096 measured that widening calls does not change the bytes or operator
work: a balanced step moved 24.66 GB in and 24.71 GB out at every width, while
64-67% of wall time remained outside the GPU operator. ADR-0108 then localized
99.34% of the accepted verifier bill inside terminal contraction.

The resident successor changes the data path rather than the call width:

- compile each target seat's 64 unique showdown half-vector pairs once and
  retain them on the GPU;
- retain the fixed belief mixture, half products, and hand-index tables;
- upload only the candidate's small unary-factor tables per seat read;
- generate all weighted half products on-device;
- construct each feature batch, apply both incidence maps, and fold the result
  into terminal records on-device; and
- return only the accumulated numerator and reach records needed by the exact
  CPU public-tree reverse pass.

Every operation remains Float64. The CPU topology, automata, hand folding, and
fixed-envelope logic remain authoritative.

## Frozen code and artifacts

The primary parent is
`experiments/results/h32-policy-delta-verifier-audit-v1.json`, SHA-256
`2fb53315812ee2afeb2d3d50399770140c1fcd0e4bb29e4d6cc54ca19743a489`.
Its config SHA-256 is
`ea0cd0840de3a2fc31114963ae45dd8b3d3ca6a4906fdaff585a78001d79bb4b`.
Parsing that parent config revalidates the complete transitive source chain.

The new frozen files are:

| File | SHA-256 |
|---|---|
| `src/pontius/resident_heterogeneous_leaf_contraction.py` | `d1680c43b74b6f3b70c2ca9b4cdd41bc96f478102eea18c3dfb07c9866d4f4db` |
| `src/pontius/resident_leaf_adjoint_evaluation.py` | `45fc76a9bea2292926c7bff1079172a8abfc27b53cefa41bad24da836e58f470` |
| `src/pontius/h32_resident_verifier_audit.py` | `fa5997ba29c096cafaa7f5675e8e043e60c193ec0947ad3cefeb056bedc09555` |
| `experiments/configs/h32-resident-verifier-audit-v1.json` | `13eaaa72501514eb51fd6f7734598d316f2724f5b89b26be1e7d860c24a406c4` |

The result target is
`experiments/results/h32-resident-verifier-audit-v1.json`.

The complete repository suite passes 497/497 before freeze, including four
live optional-CuPy tests.

## Frozen h32 workload

Reproduce ADR-0108 exactly:

- six seats and 32 hands per seat;
- balanced and blocker-heavy factor beliefs;
- local-blocker and all-seat-strength target shifts;
- board `2c 7d 9h Js Qc`;
- equal stacks, one bet size, and the 385-node one-bet river public tree;
- the canonical 13-policy candidate order;
- seat order `0,1,2,3,4,5`;
- maximum feature width 384; and
- the same fixed blueprint caps and `3e-9` raw guard.

The expected result remains 52 candidate rows, 133 evaluated seats, 13
completed candidates, and the four ADR-0108 selected digests. These counts are
known parent semantics, not new evidence.

## Conservative cache charge

Compile and charge one complete resident cache per target:

- one resident belief workspace; and
- all six response-seat automaton libraries.

Do not share a cache between the two target shifts, even though the static
automata and board would permit it. This intentionally models a one-target
decision and prevents the two audit shifts from subsidizing one another.

The cache compilation bill includes CPU automaton-half construction, all
host-to-device uploads, synchronization, and allocation. Sparse incidence
operator upload and target-belief compilation are common to resident and
incumbent paths and remain outside both candidate bills, as in ADR-0108.

The charged resident bill is:

`six-seat resident cache compile + all 13 acceptance-aware candidate reads`.

Report the marginal bill separately, but only the charged bill enters the
speed gates.

## Incumbent calibration

The incumbent bill is the measured ADR-0108 partial-verifier bill for the same
target and exact seat prefix. Control same-day runtime drift by rerunning its
complete `search_average1` candidate through the legacy transferred path.

Scale the parent bill by:

`live legacy search_average1 wall / parent search_average1 wall`.

Require the ratio to remain in `[0.5, 2.0]`. This avoids rerunning all 133
legacy seat reads while retaining a contemporaneous complete six-seat control.
The resident search-average-one row is still charged normally inside its
portfolio.

## Fresh-board transfer control

Before the h32 target rows, build an undisclosed h7 balanced case on board
`3s 8c Th Kd Ac`. Evaluate uniform policy for response seats zero and three,
which exercises both incidence directions.

For each seat, compare resident and transferred-GPU profile utility,
best-response value, and chosen response. Report marginal and cache-charged
speed and transfer bytes. Exactness is gated at `1e-9`; speed is diagnostic
only. A two-seat h7 control cannot authorize a fresh-board h32 performance
claim, but it can catch board-specific indexing or cache-provenance failures
before the primary result is interpreted.

## Frozen gates

The result passes only if:

1. the parent, config, requirements, resident modules, audit implementation,
   environment, and all transitive parent hashes reproduce;
2. the audit produces exactly four targets, 52 candidates, 133 live seat
   evaluations, 13 completed candidates, and two fresh-board control rows;
3. all 52 reconstructed policy digests match the frozen teachers;
4. fresh-board utility and best-response errors are at most `1e-9`;
5. h32 utility, best-response, deviation-gain, completed NashConv, and
   completed zero-sum errors are each at most `1e-9`;
6. every h32 stop prefix and final selected digest matches ADR-0108;
7. pooled and both family charged, calibrated speedups are at least `1.5x`;
8. all four calibration ratios remain in `[0.5, 2.0]`;
9. every resident seat read is at most 60 seconds and every complete static
   cache compile is at most 120 seconds;
10. estimated host numeric peak is at most 3 GB and CuPy pool peak is at most
    12 GB; and
11. total audit wall time is at most 1,200 seconds.

No strategy-quality or candidate-acceptance outcome is a gate. The mechanism
must be allowed to fail economically while remaining exact.

## Required telemetry

Report per target:

- one-shot cache compile, CPU half preparation, device upload, and bytes;
- calibrated incumbent, resident marginal, and resident charged bills;
- probability compilation, factor preparation/upload, device product
  generation, resident sparse/fold pipeline, result download, hand fold, and
  public-tree reverse time;
- derived legacy-equivalent H2D/D2H bytes and actually charged resident bytes;
- marginal and charged speedups;
- exact stop and selection identities; and
- host and device resource peaks.

Pooled reporting must include family speedups and the total charged byte
reduction. Call count alone is not an accepted explanation.

## Pre-freeze disclosure

No h32 resident timing or h32 resident value has been observed.

The disclosed development controls are:

- a 12-terminal h4 resident contraction matches transferred CuPy terminal
  reaches to `2e-13` and numerators to `2e-12`;
- a complete h4 resident seat matches utility, best response, gain, and action
  map;
- one balanced h7 seat on the original development board measured 204.73 ms
  transferred versus 114.54 ms resident, or `1.787x` marginal and `1.717x`
  including its 4.72 ms cache;
- that h7 control had utility error `2.22e-16`, best-response error zero, and
  reduced marginal transfer from 26.85 MB to 0.865 MB; and
- static h32 shape inspection, without running the resident kernel, found
  six-seat half-vector totals of 4.325 GB balanced and 2.960 GB blocker-heavy.

The h7 timing motivated but did not set the h32 threshold. The `1.5x` gate is
frozen above noise and below the development result, with a much more
conservative six-seat one-target cache charge.

## Decision branches

- If exactness, stop identity, or selection identity fails, reject the resident
  evaluator regardless of speed.
- If resource gates fail, retain the transferred partial verifier and redesign
  cache residency or seat scheduling.
- If exactness passes but charged speed is below `1.5x`, retain the code as an
  experimental backend and do not replace ADR-0108.
- If all gates pass, make the resident partial verifier the h32 systems
  incumbent and use its new phase bill—not ADR-0096's obsolete transferred
  bill—to choose the next native optimization.
- Do not infer wider-tree or full-NLHE transfer from a pass. The next strategic
  scale test must still widen public actions or board coverage.

## Dissent protocol

**Confidence:** extremely high in the algebra and parent semantics; high in
small-axis exactness; moderate in h32 speed and memory-pool behavior.

**Opposing evidence:** CuPy still launches and allocates per feature batch. It
removes transfer and host folding but is not a fused custom CUDA kernel. GPU
feature construction can simply replace the removed CPU bottleneck.

**Largest risk:** keeping all six automaton libraries resident fragments the
CuPy pool or pushes later sparse temporaries above the 12 GB gate. Static byte
arithmetic is necessary but not sufficient to predict allocator behavior.

**Cheapest falsification:** the fresh-board h7 control rejects index or
direction errors before h32; the first balanced h32 target rejects accuracy,
memory, or target-level economics before pooled claims are considered.
