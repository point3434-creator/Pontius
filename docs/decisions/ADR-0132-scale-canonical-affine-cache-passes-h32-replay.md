# ADR-0132: The scale-canonical affine cache passes h32 replay

## Status

ADR-0131 executed from clean commit `7bbcf70`.  All sixteen frozen gates passed,
exactly zero h32 steps ran, and no strategy-quality evaluator was called.

## Evidence identity

The 34,652-byte artifact is
`experiments/results/h32-canonical-affine-cache-replay-v1.json`, SHA-256
`9bc385bd463ffd39a8ff587edf58a75ca7663b3ec1d25c90cad3309e8c315349`.
Its configuration SHA-256 is
`d334f18cf13caa617e9ce152a004f7dcb0d85e90766f64a3944779a4bbba644a`.
The run recorded strict clean Git state at
`7bbcf70d88cfc2c818041186f6145a1216670676` and completed in
`98.6809 s`.

The failed ADR-0129 parent was bound exactly: its only failed gate was the
384-versus-378 basis count, its single widened step had already executed, and
its strategy-quality claim was null.  The successor therefore performed only
cache construction and accounting.

## Identity and correctness result

The scale-canonical cache restored exactly 378 shared bases for all 762 logical
automata in both range families.  Host geometry and every device cache agreed.
The explicit h2 five-way-tie family shared one identity across final pots 12,
30, and 48, while a changed final-mode strength basis remained distinct.

Production compilation reconstruction-checked every grouped member.  The h2
complete raw-versus-canonical DCFR control had exactly zero regret and
average-sum disagreement.  At h32, raw-equivalent automaton bytes reproduced
ADR-0128 exactly:

- balanced: `8,248,132,672` bytes;
- blocker-heavy: `6,759,693,248` bytes.

Logical middle rank and maximum rank also remained exact:

| Family | Logical rank | Stored canonical rank | Maximum rank | Bases |
|---|---:|---:|---:|---:|
| Balanced | 20,648 | 10,058 | 105 | 378 |
| Blocker-heavy | 19,432 | 9,466 | 99 | 378 |

Relative to ADR-0130's scale-sensitive cache, canonical identity removed 532
stored rank columns balanced and 500 blocker-heavy.  This closes the failed
representation gate without changing logical contraction width.

## Persistent storage

Persistent bytes include one resident belief and all six target-seat caches.
The two shifts within each family again had identical geometry.

| Family | Raw two-size | Failed 384-basis affine | Canonical 378-basis | Canonical/raw |
|---|---:|---:|---:|---:|
| Balanced | 8,249,930,284 | 4,232,286,556 | 4,019,771,708 | 48.7249% |
| Blocker-heavy | 6,761,258,660 | 3,468,533,492 | 3,294,601,492 | 48.7276% |

Canonical identity saved a further 212,514,848 bytes balanced and 173,932,000
bytes blocker-heavy versus the failed cache.  The two-size canonical cache is
also approximately 5% smaller than the frozen one-size raw cache, because it
stores shared amount-independent bases rather than one full payload per
logical terminal group.

This is a storage result only.  The two public branches and their logical leaf
terms remain real work.

## Headroom

Both families satisfied the prior conjunctive reserve, although this replay
could not authorize arithmetic.

| Family | Pool total | Headroom below 12 GB | Physical free |
|---|---:|---:|---:|
| Balanced | 4,086,369,280 | 7,913,630,720 | 11,176,771,584 |
| Blocker-heavy | 3,353,434,624 | 8,646,565,376 | 11,912,871,936 |

Every value exceeds the frozen 5,184,456,164-byte non-cache reserve.  These
measurements confirm that the representation solves ADR-0128's residency
problem under the existing 12 GB concurrency boundary.

## Cold construction cost

Canonical cold construction was materially slower than ADR-0130's
Float64-digest cache:

| Target | Canonical cold time | Ratio to failed cache |
|---|---:|---:|
| Balanced / local blocker | 24,517.080 ms | 1.5816x |
| Balanced / strength | 24,569.263 ms | 1.5374x |
| Blocker-heavy / local blocker | 20,401.875 ms | 1.5507x |
| Blocker-heavy / strength | 21,378.608 ms | 1.5543x |

Semantic share classification and repeated production identity checks charge
real host work.  Every compile remains well below the frozen 120-second limit,
but the trusted representation should not be described as a free construction
optimization.

## Step and quality boundary

The replay executed zero h32 steps under every memory outcome, exactly as
frozen.  It constructed, serialized, inspected, and evaluated no h32 policy.
Strategy-quality evaluations were zero and the result's strategy-quality claim
is null.

ADR-0130's one diagnostic step remains the only widened step: 19.616 seconds,
2.245x the matching one-size incumbent, with 9.738 GB pool high-water.  Because
that parent failed its basis-count gate, the timing remains diagnostic rather
than an accepted performance comparison.  It must not be silently promoted by
this cache-only successor.

## Decision

Accept the scale-canonical affine cache as the exact h32 representation for
two-size resident terminal payloads.  It restores the intended 378 semantic
bases, preserves raw-equivalent accounting and logical ranks, and satisfies the
existing memory boundary.

Reject the raw two-size cache and the 384-basis Float64-digest cache as h32
production candidates.  Retain both as historical controls.

Do not run another widened step, train a two-size blueprint, evaluate a sized
policy, or claim that the added action improves strategy.  The representation
question is closed; decision quality per wall-clock second remains unmeasured
and requires a new explicit research question rather than another systems
preflight.

## Dissent

**Confidence:** very high in identity, byte accounting, and headroom; high in
the cache-only acceptance; low in any strategy value for the second action.

**Opposing evidence:** cold construction is roughly 1.54–1.58x slower than the
failed cache, and the only widened-step diagnostic was 2.245x the one-size wall
bill.  Storage sharing does not remove duplicated public reach or contraction
work.

**Largest unknown:** whether a second river size earns approximately twice the
logical systems work on a broader, preregistered strategy corpus.

**Cheapest falsification:** not another resident step.  First define an honest
wall-clock-matched quality experiment with a fixed incumbent, fixed total
construction and planning budget, and no reuse of this systems result as a
quality prior.
