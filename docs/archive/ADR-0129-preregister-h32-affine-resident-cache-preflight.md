# ADR-0129: Preregister the h32 affine resident-cache preflight

## Status

Frozen after ADR-0128 and affine-basis identity hardening, and before any h32
affine-cache byte, pool, middle-rank, construction-time, or step measurement.

## Context

ADR-0128 measured the raw two-size h32 cache at 6.761–8.250 GB of persistent
numeric storage.  Neither range family satisfied the unchanged 5.184 GB
non-cache reserve below the 12 GB CuPy-pool ceiling, so the frozen branch ran
zero widened steps.  Small h2 controls then established that an exact affine
cache can store one amount-independent left transition basis and normalized
winner-share basis per topology, plus final-pot and sunk-value coefficients
per logical automaton.

The subsequent independent review exposed a latent cache-key defect: the
original grouping digest bound transition and bond tables but not the
final-mode winner-share basis.  Two automata could therefore share the old key
while requiring different right bases.  Commit `cfb4ca6` now binds the
amount-normalized terminal winner values and reconstruction-checks every group
member during production compilation.  The h32 cache is not trusted until the
new identity and accounting survive this separately frozen replay.

The frozen configuration is
`experiments/configs/h32-affine-resident-cache-preflight-v1.json`, SHA-256
`903b904b285f10e9ecf7134873c23e4eff368f54e387265dab18e5580fc0f825`.
The additive runner is
`src/pontius/h32_affine_resident_cache_preflight.py`, SHA-256
`732dcd16721c2fb371a090ee7869aa728a8cb2ca4feed24d50b8649c27b28e0c`.
The hardened affine contraction is SHA-256
`f5f48f594b38ee3781398f666ce707217343cc62399df6b035d2823ea3dfd8e8`.
The result target is
`experiments/results/h32-affine-resident-cache-preflight-v1.json`.

## Frozen workload

Reuse ADR-0127's exact four h32 target beliefs and order:

1. balanced / local seat-five blocker shift;
2. balanced / all-seat strength shift;
3. blocker-heavy / local seat-five blocker shift; and
4. blocker-heavy / all-seat strength shift.

The board remains `4h 6s Td Qh As`, with six 30-chip stacks, a 12-chip pot,
opening sizes `(3, 6)`, 32 hands per seat, three mixture components, split
index three, and maximum feature width 384.  Build only the two-size affine
cache for each target: one resident belief plus all six target-seat automaton
caches.  The shared sparse GPU operators remain live and are excluded from the
cache-construction bill, matching ADR-0127.

The constructed game's `layout.game.payoff_span` must equal 48 chips.  The
stack field is never reused as a span.  If the derived value differs, the run
fails before cache allocation.

## Measurements

For every target report:

- belief, shared-basis, coefficient, automaton, and combined persistent bytes;
- raw-equivalent automaton bytes and ratios to ADR-0128's raw two-size cache;
- all 762 logical automata and their total logical middle rank;
- the 378 stored affine bases and their stored topology middle rank;
- maximum middle rank and per-seat geometry;
- half-vector preparation, upload, and complete cold construction time;
- CuPy used and total bytes before and after construction;
- headroom below the 12 GB pool ceiling and physical device free bytes; and
- construction-time and storage ratios to the frozen raw result.

The raw-equivalent byte count must exactly reproduce ADR-0128's raw automaton
bytes.  Affine persistent automaton storage must be strictly smaller.  These
are mechanism and accounting gates, not a promised compression ratio.

## Frozen headroom rule

Retain ADR-0127's conservative non-cache reserve exactly:

`9,416,577,536 - 4,232,121,372 = 5,184,456,164 bytes`.

The affine cache authorizes arithmetic only if all four measured targets leave
at least that reserve both below the 12 GB CuPy-pool ceiling and in physical
device free memory.  The rule remains conjunctive across all targets; it is
not weakened to the selected warm-step target after observing results.

If all four pass, rebuild the balanced/local-blocker cache.  The rebuilt cache
must independently satisfy the same rule immediately before arithmetic.  A
rebuild that loses headroom stops with zero steps rather than treating allocator
variation as permission.

## Conditional warm step

If and only if the measured and rebuilt affine caches are safe, execute exactly
one complete alternating resident DCFR step.  Initialize every information set
uniformly with positive regret mass equal to `0.1 * layout.game.payoff_span`,
which is 4.8 chips under the frozen game.  Report:

- marginal and reported wall time;
- summed terminal-contraction time and sparse batches;
- logical middle-rank work and maximum rank;
- maximum batch scratch and CuPy-pool high-water; and
- the wall-time ratio to the matching frozen one-size incumbent step.

Do not serialize, inspect, verify, or evaluate the resulting policy.  If any
headroom condition fails, run zero h32 affine steps and return to residency or
contraction representation rather than tune allocation order.

## Frozen gates

Before h32, the h2 raw-versus-affine complete-step control must remain within
`2e-12` for every regret and average accumulator.  It must also establish:

- 763 public nodes, 127 terminal groups, 762 logical automata, and 378 shared
  affine bases;
- exact raw-equivalent byte accounting and a strict storage reduction;
- a game-derived payoff span of 48; and
- different affine digests for equal transition tables with different
  final-mode winner bases.

The h32 run additionally requires:

- strict, fail-closed Git cleanliness and exact SHA identity for every parent,
  source, configuration, and GPU requirement;
- four targets in the frozen order with exact target descriptors and belief
  digests;
- the frozen public topology, automaton count, and 378 affine identities;
- exact equality with ADR-0128's logical total and maximum middle ranks;
- exact raw-equivalent automaton bytes and strictly lower affine storage;
- every cold cache construction within 120 seconds and below 12 GB pool total;
- exact compliance with the conditional zero-or-one-step branch;
- any executed step within 120 seconds and below 12 GB pool total;
- zero strategy-quality evaluations; and
- total wall time within 1,200 seconds.

Headroom safety remains an outcome rather than a pass gate.  A clean unsafe
measurement passes when it stops before arithmetic.

## Pre-freeze controls

Only h2 was executed before this freeze.  All 762 logical automata collapsed
to 378 hardened affine identities.  Raw-equivalent bytes were exactly 235,776;
affine basis plus coefficients used 130,704 bytes, or 55.4357% of raw storage.
The complete raw and affine DCFR steps had exactly zero regret and average-sum
disagreement.  The game-derived payoff span was 48.

The adversarial identity control held transition and bond tables equal while
changing only the final-mode winner basis.  The normalized terminal bases and
their hardened affine digests differed, as required.

No h32 affine cache has been compiled.  No h32 affine persistent byte count,
pool total, stored topology rank, construction time, step time, policy, or
quality value has been observed.

## Interpretation

- **Safe:** one systems-only widened step measures the affine marginal bill.
- **Unsafe:** zero steps; revisit residency or contraction representation.
- **Accounting mismatch:** reject the affine measurements even if memory looks
  favorable.
- **Identity or reconstruction failure:** return to cache grouping and do not
  interpret any h32 geometry.

No branch claims that a second action improves strategy, earns its work, or
belongs in a production abstraction.

## Dissent

**Confidence:** high that hardened affine storage remains materially below the
raw cache; moderate that the unchanged reserve authorizes one step; low that
the marginal step bill improves, because logical terminal work remains near
1.95x the one-size incumbent.

**Opposing evidence:** the h2 storage ratio may not transfer cleanly through
h32 allocator size classes, and production reconstruction checks add cold host
work that the original affine prototype did not charge.

**Largest unknown:** pool high-water when all 20,648 balanced logical
middle-rank columns are reconstructed and contracted through one full
alternating step.

**Cheapest falsification:** the first complete balanced affine cache.  If its
post-cache pool headroom misses the unchanged reserve, finish the remaining
frozen cache measurements but execute no arithmetic.
