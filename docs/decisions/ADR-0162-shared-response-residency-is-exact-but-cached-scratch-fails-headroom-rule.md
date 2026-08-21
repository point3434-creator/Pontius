# ADR-0162: Shared response residency is exact but cached scratch fails the headroom rule

- Status: accepted result with residency authorization withheld
- Date: 2026-08-21
- Implements: ADR-0161
- Result: `experiments/results/h32-shared-response-residency-replay-v1.json`

## Result

All fourteen mechanism gates passed from clean preregistration commit `82207f7`. One balanced h32 topology/automaton bundle served both retained target-belief shifts simultaneously. Target descriptors, blueprint policy digests, and topology identity reproduced exactly. The twelve retained blueprint seat evaluations agreed to at most `2.84e-15` in utility, `2.78e-15` in best-response value, and `7.50e-16` in deviation gain. No new strategy-quality label was created.

## Explicit storage

The shared automaton bundle contains 4,325,101,664 numeric bytes. Each target-specific belief cache adds only 1,826,160 bytes. Both response overlays together retain 826,464 identity-unique host numeric bytes.

Total explicit shared device state is therefore 4,328,753,984 bytes. Duplicating the automaton payload would require 8,653,855,648 bytes. Sharing saves 4,325,101,664 bytes and reduces the explicit two-context device bill to 50.0211% of duplication.

This confirms the intended ownership boundary: target shifts change the belief products, not the showdown topology or automaton half vectors.

## Construction bill

The shared automaton bundle compiled in 3,545.84 ms. The local-blocker context bound in 9,376.43 ms and the all-seat-strength context in 9,222.72 ms. Belief-cache upload was below 1 ms in each case; essentially all binding time was the six-seat source response construction. Total cold construction was 22,144.99 ms.

The result therefore solves storage duplication, not cold-start latency. Both contexts must be prepared before the street if they are intended to be instantly selectable.

## Frozen headroom decision

The preregistered headroom outcome is false, so two-context residency is not authorized by this result.

- Peak CuPy pool total: 7,934,734,336 bytes.
- Headroom below the 12 GB ceiling: 4,065,265,664 bytes.
- Required reserve: 5,184,456,164 bytes.
- Reserve deficit: 1,119,190,500 bytes.
- Minimum physical free memory: 7,219,445,760 bytes, which independently passes.

The mechanism is visible in the frozen snapshots. After both contexts are ready, CuPy pool used bytes are 4,398,026,752 while pool total remains 7,934,734,336. Thus 3,536,707,584 bytes are allocator-held free blocks left by source-response construction. This observation does not relax the frozen total-pool rule or convert the result into a pass.

## Decision

Accept the shared topology/automaton bundle and target-specific binding API as exact. Retain single-context residency under ADR-0161 because the conjunctive reserve outcome failed.

The cheapest next systems question is explicit cache lifecycle, not another representation. Separately preregister releasing only unreferenced CuPy pool blocks after both immutable contexts are constructed, then replay retained atomic labels across both contexts. The successor must measure pre-trim and post-trim used/total/free bytes, prove that live shared arrays remain resident and exact, and measure the pool high-water of a subsequent certificate. It may not change construction order, thresholds, targets, or labels after observing this result.

## Scope

This is systems and exactness evidence only. It does not authorize deployment, strategy selection, atom packing, union composition, new action sizes, or a strategy-quality claim.
