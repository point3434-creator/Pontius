# ADR-0128: Raw two-size h32 residency is unsafe; build the affine cache

## Status

ADR-0127 executed from clean commit `7c136c2`.  All frozen mechanism gates
passed, the raw cache failed the preregistered headroom rule, zero widened h32
steps ran, and the mandated affine/shared-topology cache now passes small exact
controls.

## Evidence identity

The 35,462-byte preflight artifact is
`experiments/results/h32-multi-size-resident-cache-preflight-v1.json`, SHA-256
`c56fedf69f6ab46342d890476c5e66d711de8d1cfcc2f675d77ddb21b871cbfd`.
Its configuration SHA-256 is
`d3a1c0af41334b48aa07dcb10f73b7671d7cf22f29f822f8333bca55b5795aae`.
The run recorded a clean Git state at
`7c136c2bb19269688e80aedf2aa675590be43f43` and completed in `46.9819 s`.

All fourteen named gates passed.  The four target descriptors and belief
digests reproduced exactly, the h2 complete-step control passed, both public
topologies and automaton counts matched, transition topology and maximum-rank
invariance held, every cold construction stayed below the resource ceilings,
and the conditional branch correctly executed zero widened steps.  No strategy
quality evaluator was called.

## Raw persistent bill

Persistent bytes below include one resident belief and all six target-seat
terminal half-vector caches.  Target shifts within a family have identical
geometry, as expected.

| Family | One size | Two sizes | Ratio |
|---|---:|---:|---:|
| Balanced | 4,232,121,372 | 8,249,930,284 | 1.949361x |
| Blocker-heavy | 3,468,378,036 | 6,761,258,660 | 1.949401x |

The one-size-to-two-size increase is therefore approximately 4.018 GB on the
balanced axes and 3.293 GB on the blocker-heavy axes.  It repeats ADR-0126's
h4/h7 ratio at the actual h32 customer.

Host automaton objects are not the issue.  Balanced raw automata grow from
10,166,360 to 19,813,888 bytes and blocker-heavy from 9,324,904 to 18,174,416
bytes.  Device half vectors dominate persistent residency because every half
assignment record carries every reachable middle state.

## Middle-rank width

The logical contraction width nearly doubles while maximum width is invariant.

| Family | One-size total | Two-size total | Ratio | Maximum, both |
|---|---:|---:|---:|---:|
| Balanced | 10,590 | 20,648 | 1.949764x | 105 |
| Blocker-heavy | 9,966 | 19,432 | 1.949829x | 99 |

Both widths still contain exactly 378 distinct transition topologies.  The
one-size libraries contain 384 logical automata and the two-size libraries 762.
The extra size adds amount-specific leaf terms and therefore real contraction
work; structural sharing removes storage duplication, not the two public
branches or their logical feature width.

## Cold construction bill

| Target | One size | Two sizes | Ratio |
|---|---:|---:|---:|
| Balanced / local blocker | 3,437.600 ms | 6,925.066 ms | 2.014506x |
| Balanced / strength | 3,452.031 ms | 6,615.812 ms | 1.916499x |
| Blocker-heavy / local blocker | 3,227.178 ms | 6,031.786 ms | 1.869059x |
| Blocker-heavy / strength | 3,150.725 ms | 6,030.234 ms | 1.913920x |

These are cold Python/CuPy construction bills with shared sparse-operator
upload excluded from both arms.  They are not production latency claims.

## Headroom decision

The frozen non-cache reserve was `5,184,456,164` bytes.

- Balanced two-size caches left `3,683,565,056` bytes below the 12 GB pool
  ceiling, a `1,500,891,108`-byte deficit.  Physical free memory was
  `6,565,134,336` bytes.
- Blocker-heavy two-size caches left `5,180,043,264` bytes below the ceiling,
  missing the reserve by only `4,412,900` bytes.  Physical free memory was
  `8,066,695,168` bytes.

The rule was conjunctive across all four targets.  Both families therefore
failed safety even though both raw caches compiled and physical memory could
probably sustain some laboratory arithmetic.  The preflight stopped before a
step exactly as frozen.  Allocation order is not tuned and the near-miss on the
blocker family is not rounded into a pass.

## Affine/shared-topology implementation

The additive cache implementation is
`src/pontius/affine_resident_heterogeneous_leaf_contraction.py`, SHA-256
`0a21af3a0cbaf30695c73874cecea97ddc42eca06b0f95403bcaecf81a5b36f6`.
The sized CFR bridge is
`src/pontius/multi_size_affine_resident_leaf_adjoint_cfr.py`, SHA-256
`804e23dfa22bf1256f1fbfa5960e68b052643a42104081659f07cd81b1da4c9c`.

For fixed contenders and target, the cache now stores:

1. one amount-independent left transition basis;
2. one normalized right winner-share basis; and
3. per-logical-automaton coefficients for final-pot scale and sunk value.

At contraction time, the right slice is reconstructed as the winner-share
basis scaled by `final_pot`, with its constant column scaled by `sunk_value`.
No amount-specific full half vector remains persistent.  This represents the
literal payoff algebra rather than fitting a low-rank approximation.

On the h2 implementation control, all 762 logical two-size automata collapse to
378 shared device bases.  Raw automaton-cache half vectors used 235,776 bytes;
the affine bases plus 14,736 bytes of coefficients use 130,704 bytes, or
55.4357% of raw storage, a 44.5643% reduction.  Every reconstructed half vector
matches within `1e-13`.  Both incidence directions and a complete alternating
DCFR step match the raw resident path within `2e-12` for reaches, action
numerators, regrets, and average accumulators.

The complete suite now passes 535 tests in 80.619 seconds.

## Decision

Reject the raw two-size cache for an h32 warm step under the established 12 GB
pool/concurrency boundary.  Retain the raw cache as an exact small-axis teacher.

Accept the affine/shared-topology cache as an implementation candidate at h2.
Do not infer its h32 bytes, pool headroom, cold cost, or marginal step bill from
the small ratio.  Those are unobserved and require a separately SHA-pinned h32
cache preflight before any affine h32 allocation.

Do not train or evaluate a two-size blueprint.  No result here measures whether
the second action improves strategy, earns its logical contraction bill, or
belongs in a production abstraction.

## Dissent

**Confidence:** very high in the raw-cache rejection under the frozen rule;
high in the exact affine algebra and small controls; moderate that h32 affine
storage will retain approximately the small-axis ratio; low that marginal
two-size step time improves, because logical terms and total rank remain near
1.95x.

**Opposing evidence:** the blocker-heavy raw cache missed by only 4.4 MB, and
both raw caches fit physical memory.  A looser single-job laboratory rule would
have run.  That does not satisfy the existing 12 GB headroom contract.

**Largest unknown:** allocator high-water and runtime cost when affine slices
are reconstructed across all 20,648 logical middle-rank columns at h32.

**Cheapest falsification:** a separately frozen affine-cache-only h32 replay on
the same four targets.  If its exact persistent bytes and post-cache pool fail
the unchanged reserve, do not attempt a step.
