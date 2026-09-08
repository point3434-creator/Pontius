# ADR-0139: The second-board canonical cache is safe for preregistered quality

## Status

ADR-0138 executed once from clean commit `bc9bc11`.  Every frozen mechanism
gate passed, all eight one-size/two-size cache rows passed the conservative
headroom rule, and zero h32 steps, policies, or quality evaluations ran.

## Evidence identity

The 25,606-byte artifact is
`experiments/results/h32-second-board-resident-cache-v1.json`, SHA-256
`749e002d1ae1cf9c76d5636711e2225f812beb0d3d28b56a379dc53a683f67bf`.
Its configuration SHA-256 is
`d1ffcc6f2f1a5b40e013d43bb507aea308529e7ae7ec6951d7aa947fe916a9ea`;
its implementation SHA-256 is
`0b9275030c6fd2e7fd1c5c56dba79a5485a31d8ea46bcddac54c7ad75792ef40`.

Strict Git metadata records clean full commit
`bc9bc11ab96ee6cec021d436f26d210fb8a0cbe7`.  The complete preflight took
`109.0809 s`, below its 1,200-second ceiling.  Every pinned source, original-
board target digest, field-set projection, topology, basis, rank, payoff-span,
construction, pool, and zero-work gate passed.

The h2 control again produced exact embedded profile utility, quality error
`3.553e-15`, zero-sum residual `1.645e-15`, 378 scale-canonical bases, and an
exact compact-policy round trip.

## Resident result

Target shifts within a family have identical resident geometry.  Timings below
show the observed range across the two arm orders.

| Family | Arm | Persistent bytes | Total / maximum middle rank | Pool total | Pool-ceiling headroom | Physical free | Cold construction |
|---|---|---:|---:|---:|---:|---:|---:|
| balanced | one size | 4,326,927,824 | 10,658 / 104 | 4,396,198,912 | 7,603,801,088 | 10,772,021,248 | 3.589–3.613 s |
| balanced | two size | 4,109,580,976 | 20,780 / 104 | 4,179,146,240 | 7,820,853,760 | 11,008,999,424 | 24.483–24.595 s |
| blocker-heavy | one size | 2,961,537,356 | 8,176 / 80 | 3,022,734,848 | 8,977,265,152 | 12,240,027,648 | 2.493–2.494 s |
| blocker-heavy | two size | 2,814,683,180 | 15,946 / 80 | 2,876,165,632 | 9,123,834,368 | 12,397,314,048 | 16.807–17.960 s |

The two-size scale-canonical representation uses approximately 94.98% of the
one-size persistent bytes even though its logical total middle rank is about
1.95x wider.  It stores 762 logical automata in 378 bases; the one-size cache
stores 384 raw logical automata.  Maximum middle rank remains identical within
each target, as frozen.

Cold construction is the cost of sharing: two-size construction is
`6.74x–7.20x` the matching one-size construction.  This repeats the first
board's qualitative result—canonical residency saves bytes, but production
member reconstruction makes it expensive to build.

## Headroom decision

The required reserve was `5,184,456,164` bytes in both pool-ceiling headroom
and physical free memory.  The weakest row is balanced one-size pool headroom
at `7,603,801,088` bytes, leaving `2,419,344,924` bytes above the reserve.
The weakest two-size row leaves `7,820,853,760` bytes below the pool ceiling,
or `2,636,397,596` bytes above reserve.

All eight rows therefore pass conjunctively.  This authorizes a separately
preregistered strategy audit to attempt its frozen arms; it does not itself
authorize an unregistered step or imply that a second size is worthwhile.

## Zero-work result

The artifact records exactly:

- h32 steps executed: zero;
- h32 policies constructed: zero;
- h32 strategy-quality evaluations: zero; and
- strategy-quality claim: null.

Only the previously frozen h2 correctness policy was exercised.  No original-
board h32 one-size blueprint was embedded in a two-size game, and no h32 sized
policy or common-game label existed at the end of this preflight.

## Decision

Accept scale-canonical cache portability to the second board under the
established laboratory reserve.  Preserve raw one-size residency and canonical
two-size residency as the two planning arms.

Next, preregister one wall-clock-matched second-board quality audit before
constructing the first original-board h32 sized policy.  Reuse ADR-0134's
90-second arm clock, complete-step reserve, candidate stream, common-game
embedding, exact fixed-envelope verifier, arm alternation, and outcome-neutral
gates.  Bind the original average-64 blueprint and the four exact ADR-0138
target digests.

The original board's historical one-size outcome is known and must be
disclosed.  It must not become a gate, a target filter, or a reason to alter
the candidate stream.  The successor top-level strategy-quality claim should
remain null; this is a revealed-board action-width replication, not independent
population evidence.

## Dissent

**Confidence:** extremely high in the measured cache safety and zero-work
contract; high that a later arm can allocate under the same reserve; low that
memory safety predicts action-width quality.

**Opposing evidence:** the original-board balanced family is 307 MB larger
than the fresh-board balanced canonical cache, while its blocker-heavy family
is 480 MB smaller.  Board geometry transfers directionally, not as a tight
byte bound.

**Largest unknown:** whether the known one-size local-target directions remain
inside the immutable caps after embedding into the wider game, and whether two-
size planning can exploit the added branch within only two or three complete
steps.

**Cheapest falsification:** the frozen balanced/local target.  It has the
largest cache and a historically useful one-size direction; a common-game cap
failure or two-size abstention there sharply limits the replication story.
