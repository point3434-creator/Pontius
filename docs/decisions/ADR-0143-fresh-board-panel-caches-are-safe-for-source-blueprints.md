# ADR-0143: Fresh-board panel caches are safe for source blueprints

## Status

ADR-0142 executed once from clean commit `853a2bb`.  Every frozen mechanism
gate passed, all 24 one-size/two-size cache rows passed the conservative
headroom rule, and zero panel h32 steps, policies, or quality evaluations ran.

## Evidence identity

The 74,427-byte artifact is
`experiments/results/h32-fresh-board-panel-cache-v1.json`, SHA-256
`1fcfeddb80f27d9bb7c6a17999d10f6e27ede81f5e762490f66784d628b801af`.
Its configuration SHA-256 is
`a0a23a739098f5286e3df1fd0f4e1ec85cd2ad723551382fe51b57a7be9a4b4d`;
its implementation SHA-256 is
`6dffdb09f105f0159c3216a6ae360111027840c68cbff59189ad6b4a43aac425`.

Strict Git metadata records clean full commit
`853a2bbbc688f178c941226624f65f745d382bbf`.  Total wall time was
`359.1573 s`, below the 1,800-second ceiling.  The seed commit, exact sampler,
three disjoint boards, six source beliefs, twelve target beliefs and
descriptors, topology, basis counts, ranks, payoff spans, arm order, resource
ceilings, and zero-work contract all reproduced.

The h2 control again produced exact embedded profile utility, quality error
`3.553e-15`, zero-sum residual `1.645e-15`, 378 canonical bases, and an exact
compact-policy round trip.

## Resident result

Target shifts within each board/family source have identical resident
geometry.  Cold timings show the observed two-target range.

| Board | Family | Arm | Persistent bytes | Total / maximum middle rank | Minimum pool headroom | Cold construction |
|---|---|---|---:|---:|---:|---:|
| panel 1 | balanced | one size | 3,010,580,808 | 7,554 / 76 | 8,922,234,368 | 2.679–2.860 s |
| panel 1 | balanced | two size | 2,860,936,360 | 14,732 / 76 | 9,071,583,744 | 18.542–19.267 s |
| panel 1 | blocker-heavy | one size | 2,710,706,208 | 7,452 / 73 | 9,227,366,912 | 2.462–2.576 s |
| panel 1 | blocker-heavy | two size | 2,576,314,160 | 14,534 / 73 | 9,361,463,296 | 16.750–17.040 s |
| panel 2 | balanced | one size | 5,100,927,240 | 12,696 / 119 | 6,830,841,344 | 4.436–4.652 s |
| panel 2 | balanced | two size | 4,844,884,056 | 24,754 / 119 | 7,086,606,336 | 31.496–31.660 s |
| panel 2 | blocker-heavy | one size | 4,389,856,080 | 12,072 / 116 | 7,548,042,240 | 3.930–3.952 s |
| panel 2 | blocker-heavy | two size | 4,169,760,960 | 23,538 / 116 | 7,767,848,960 | 27.866–28.173 s |
| panel 3 | balanced | one size | 4,307,138,224 | 10,658 / 105 | 7,623,835,648 | 3.852–3.927 s |
| panel 3 | balanced | two size | 4,090,786,192 | 20,780 / 105 | 7,839,894,528 | 25.353–27.413 s |
| panel 3 | blocker-heavy | one size | 2,940,988,424 | 8,294 / 81 | 9,001,756,160 | 2.713–2.764 s |
| panel 3 | blocker-heavy | two size | 2,795,105,032 | 16,176 / 81 | 9,147,355,648 | 18.706–18.960 s |

Across all six board/family sources, the two-size canonical cache uses
`94.9769%–95.0422%` of matching one-size persistent bytes while carrying
approximately `1.95x` total logical middle rank.  Maximum middle rank remains
identical within every comparison, and every two-size row stores 762 logical
automata in 378 canonical bases.

Cold construction remains the price of sharing: two-size construction is
`6.484x–7.191x` the matching one-size construction.  The qualitative systems
result now reproduces across five total sized boards: canonical sharing saves
about 5% of resident bytes but is substantially slower to build.

## Headroom decision

The required reserve is `5,184,456,164` bytes in both pool-ceiling headroom and
physical free device memory.

The weakest pool row is panel-2 balanced one-size at `6,830,841,344` bytes,
leaving `1,646,385,180` bytes above the reserve.  The lowest observed physical
free memory is `9,891,217,408` bytes, leaving `4,706,761,244` bytes above the
reserve.  All 24 rows therefore pass conjunctively.

Panel 2 is materially wider than the other sampled boards: its balanced source
reaches maximum middle rank 119 and a 5.101 GB one-size cache.  This validates
the decision to preflight the complete panel rather than extrapolate from the
two earlier boards.

## Zero-work result

The artifact records exactly:

- panel h32 steps executed: zero;
- panel h32 policies constructed: zero;
- panel h32 strategy-quality evaluations: zero; and
- strategy-quality claim: null.

Only the previously frozen h2 correctness policy was exercised.  No panel h32
source blueprint or sized policy exists at the end of this preflight.

## Decision

Accept raw one-size and scale-canonical two-size cache portability across the
deterministic fresh panel.  The memory result authorizes a separately
preregistered source-blueprint stage over all six board/family sources.

That successor must freeze, before execution:

- one identical solver, initialization, checkpoint schedule, and stopping rule
  across all six sources;
- the exact source-policy point used as the immutable blueprint;
- complete state and policy serialization identities;
- source-only quality accounting, if any, with no target belief constructed in
  the same run; and
- no action-width or target-quality claim.

Do not begin target adaptation, construct a two-size policy, or inspect a panel
target quality label during source generation.  The source stage is another
causal boundary, not administrative overhead.

## Dissent

**Confidence:** extremely high in the measured cache geometry and zero-work
contract; high that all six sources can allocate under the same reserve; low
that memory safety predicts whether their later candidates will certify.

**Opposing evidence:** panel 2 consumes roughly 1 GB more than the prior
largest cache, reducing the reserve margin substantially.  Concurrent
production residency remains unproven even though sequential laboratory work
is safe.

**Largest unknown:** the cost of creating six independent source blueprints.
The prior average-64 trajectories required tens of minutes per board/family
pair, so a full panel source stage is likely measured in hours rather than
minutes.

**Cheapest falsification:** preregister source generation with periodic exact
checkpointing and a hard whole-step wall-time ceiling.  A numerical, restart,
or resource failure should stop that source without exposing any target label.
