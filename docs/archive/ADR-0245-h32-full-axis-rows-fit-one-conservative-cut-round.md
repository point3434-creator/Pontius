# ADR-0245: h32 full-axis rows fit one conservative cut round

- Status: accepted engineering result; label-free h32 master prototype authorized
- Date: 2026-08-22
- Implements: ADR-0244
- Clean preregistration commit: `fe26d7e338e22c5e55d2a495d651ffda73ee304c`
- Result: `experiments/results/h32-one-seat-open-axis-preflight-v1.json`
- Result SHA-256: `1baa4ae297c5054dde63efbaed3b50729f6d56f6cf5778b9c2346ec4ec46214f`

## Result

The frozen one-seat h32 preflight passed every identity, topology, provenance,
runtime, memory, immutable-emission, and no-label gate on its first GPU
invocation. It authorizes only the label-free master prototype.

An earlier invocation stopped before CUDA initialization because the shell had
not set the runbook's pinned `PONTIUS_CUDA_DLL_DIRECTORY`. It wrote no artifact,
constructed no h32 context, and ran no coefficient pass. The recorded
invocation used the identical clean commit and configuration with only the
required repository-local CUDA 13 DLL directory initialized, matching the
established ADR-0212 and ADR-0235 precedent.

## Exact full-axis rows

All six profile passes and five fixed-response passes completed. Acting seat 0
owns the frozen 16 public nodes, 512 h32 information sets, and 1,024 action
entries per row. The six retained gain rows occupy `49,200` bytes.

Projection against all 16 frozen regret-vertex directions produced 96 teacher
comparisons:

| Identity | Maximum error |
|---|---:|
| Source row | `5.13e-16` |
| Source zero sum | `4.44e-16` |
| Profile slope | `4.14e-15` |
| Fixed-response slope | `3.25e-15` |
| Gain slope | `8.88e-16` |

Every result is more than three orders of magnitude below the frozen `2e-11`
ceiling. All six exact row digests are distinct, all five exact response
signatures are distinct, and explicit external-axis response coverage passed.

The six gain rows have numerical rank five. The effective condition number on
the nonzero singular spectrum is `1.383`, and minimum normalized pairwise
separation is effectively one. The dependency is recorded; no row was removed
or merged.

## Cost and memory

Cold resident setup took `9,119.53 ms` and is reported off-clock. Within the
resident live ledger:

- the accepted warm step took `1,637.56 ms`;
- the eleven initial row passes took `2,880.25 ms`;
- the five response-row passes contributed `1,304.53 ms`; and
- the measured six-seat source-response oracle took `2,307.66 ms`.

The maximum middle rank was 119 and maximum reported pass peak numeric storage
was `110,319,944` bytes. The CuPy pool peaked at `5,661,330,944` bytes, while
physical free device memory never fell below `9,629,073,408` bytes. Memory is
not the binding resource.

The 16-direction teacher took `1,910.87 ms` after the capacity decision and is
not charged to the resident live path.

## Exactly one conservative round

Applying the frozen 1.25 safety factors gives:

- response-oracle and separate final-certificate reserve: `2,884.57 ms`;
- five new response-row reserve per round: `1,630.66 ms`;
- master reserve per round: `500 ms`;
- complete cut round: `5,015.23 ms`; and
- fixed ledger before cut rounds: `8,452.38 ms`.

One complete round therefore costs `13,467.62 ms` and leaves `1,532.38 ms` of
the hard street boundary. A second complete round does not fit. This is the
central result: full-axis construction is feasible, but live convergence has
not been shown and the available iteration budget is one.

The h4 controls required three and five generated-solve iterations from their
respective initial libraries. Those counts are not h32 predictions, but they
make it especially important that the successor report whether its first
restricted master is already certified or whether one oracle round closes the
gap. No multi-round optimism is imported.

## Decision

Authorize one label-free h32 master prototype on the identical target, acting
seat, row families, and external axes. It must:

1. build the source row library and solve the restricted master;
2. independently evaluate the proposed policy with the exact six-seat
   response oracle;
3. add every violated opponent response row in one multi-cut round;
4. resolve once, then stop regardless of remaining gap;
5. report restricted-master `L`, independently evaluated incumbent `U`,
   `U - L`, active caps, exact response signatures, added rows, master and
   oracle timings, retreat behavior, memory, and the complete measured ledger;
   and
6. emit only the immutable blueprint and execute no strategy-quality label.

If the initial master or the single allowed multi-cut round closes `U - L` to
the frozen tolerance, a later preregistration may ask a strategy-quality
question with an independent exact final certificate. Otherwise reject this
live solver at the current cost structure and retain it for off-clock analysis
or future oracle/row reductions. Do not borrow a second round from the final-
certificate or emission reserve.

## Claims boundary

This is an engineering identity, memory, and one-round capacity result on one
target and one acting seat. No optimizer-convergence, strategy-quality,
multiplayer-safe, deployment, composition, cross-street, population, or broad
poker-strength claim is made.
