# ADR-0131: Preregister the h32 scale-canonical affine-cache replay

## Status

Frozen after ADR-0130's failed basis-count gate and before any h32
scale-canonical cache byte, pool, stored-rank, or construction-time
measurement.

## Context

ADR-0129's h32 cache used a digest over Float64 values produced by dividing
terminal payoffs by final pot.  Five-way winner shares differed by one ULP
across pots 12, 30, and 48, so the supposedly amount-independent cache stored
384 bases instead of the frozen 378.  Although every reconstruction and all
other gates passed, ADR-0130 correctly rejected the aggregate result.

The additive canonical cache encodes each terminal winner share by its semantic
class: zero or tie multiplicity `1..N`.  It then constructs a canonical
Float64 basis from `1 / multiplicity` and still reconstruction-checks every
group member against its original half vector.  Genuinely different final-mode
winner bases remain distinct.

The frozen configuration is
`experiments/configs/h32-canonical-affine-cache-replay-v1.json`, SHA-256
`d334f18cf13caa617e9ce152a004f7dcb0d85e90766f64a3944779a4bbba644a`.
The additive runner is
`src/pontius/h32_canonical_affine_cache_replay.py`, SHA-256
`86bcf7b582dbbb654f716bcd9889ea58c8c1a3e42dfa7f5c5e3e69345eac61dc`.
The canonical cache implementation is
`src/pontius/canonical_affine_resident_automaton_cache.py`, SHA-256
`5d722bff2dd55b76957c4d178a0b3aadf0f9e37f019204741894ef70875c1258`.
The result target is
`experiments/results/h32-canonical-affine-cache-replay-v1.json`.

## Frozen workload

Replay the exact ADR-0129 cache workload:

- board `4h 6s Td Qh As`;
- six 30-chip stacks, pot 12, and opening sizes `(3, 6)`;
- 32 hands per seat and three mixture components;
- balanced and blocker-heavy families;
- local seat-five blocker and all-seat strength shifts, in the same four-target
  order; and
- split index three, query chunk 256, and feature width 384.

For each target compile one resident belief and six scale-canonical two-size
automaton caches.  Keep the shared sparse GPU operators live and exclude their
construction from the cache bill, exactly as in ADR-0129.

Derive payoff span from `layout.game.payoff_span` and require 48.  Never use
the 30-chip stack field as a payoff span.

## Measurements

For each target report:

- basis, coefficient, automaton, belief, and combined persistent numeric bytes;
- 762 logical automata versus stored canonical bases;
- logical total, stored topology, and maximum middle rank;
- raw-equivalent automaton bytes;
- per-seat geometry;
- half preparation, upload, and complete cold construction time;
- pool used and total before and after construction;
- headroom below the 12 GB ceiling and physical device free bytes; and
- ratios to both ADR-0128's raw two-size cache and ADR-0130's failed
  Float64-digest cache.

The replay must recover exactly 378 canonical identities, preserve raw
equivalent bytes and logical ranks, and use strictly fewer persistent bytes and
stored topology rank than ADR-0130's 384-basis cache.

## Headroom and zero-step rule

Continue to report the unchanged prior reserve:

`9,416,577,536 - 4,232,121,372 = 5,184,456,164 bytes`.

Whether or not all four targets satisfy it, this replay executes **zero h32
steps**.  ADR-0130 already consumed the one widened-step allowance.  This
experiment repairs and measures representation identity only; memory safety
cannot reopen arithmetic without a later explicit authorization.

## Frozen gates

The pre-h32 control must require:

- exact h2 raw-versus-canonical regret and average-sum agreement within
  `2e-12`;
- 763 public nodes, 127 terminal groups, 762 logical automata, and 378 stored
  bases;
- exact raw-equivalent byte accounting and strict storage reduction;
- game-derived payoff span 48;
- one canonical identity across otherwise equal five-way-tie automata at pots
  12, 30, and 48; and
- a distinct identity after changing the final-mode strength basis.

The h32 replay additionally requires:

- the exact failed-parent artifact whose only failed gate was
  `automaton_and_basis_counts` and whose single widened step already executed;
- fail-closed clean Git state and exact SHA identity for every input and source;
- four target identities in frozen order;
- 763 public nodes, 127 terminal groups, 762 automata, and exactly 378 canonical
  identities in both host geometry and device caches;
- exact logical total/maximum rank and raw-equivalent bytes from the parent;
- strictly lower persistent bytes and stored topology rank than the failed
  384-basis cache;
- every cold compile within 120 seconds and below 12 GB pool total;
- exactly zero h32 steps and zero strategy-quality evaluations; and
- total wall time within 1,200 seconds.

Prior-rule headroom is an outcome only.  A safe result does not authorize
another step.

## Pre-freeze controls

Only h2 controls ran before this freeze.  The canonical cache stored 378 bases
for 762 logical automata.  Raw-equivalent bytes were exactly 235,776; canonical
basis plus coefficients used 130,704 bytes.  A complete raw and canonical DCFR
step had exactly zero regret and average-sum disagreement.

The explicit five-way-tie family at final pots 12, 30, and 48 produced one
canonical identity.  Changing the final-mode strength order produced a
different identity.  The constructed sized game derived payoff span 48.

No h32 scale-canonical cache has been compiled.  No h32 canonical persistent
byte count, stored rank, pool total, or cold construction time has been
observed.  No successor h32 step is authorized.

## Decision rule

- **Pass:** accept the 378-basis scale-canonical representation geometry and
  retain ADR-0130's step only as diagnostic systems evidence.
- **Count or reconstruction failure:** return to semantic basis construction.
- **Accounting failure:** reject all canonical byte conclusions.
- **Unsafe memory:** accept a correct representation result but do not infer
  deployable residency.

No outcome makes a strategy-quality claim or licenses training a two-size
blueprint.

## Dissent

**Confidence:** very high that semantic codes restore 378 identities; high in
raw-equivalent accounting; moderate in the exact h32 byte saving from removing
only six bases.

**Opposing evidence:** the extra six bases are a small fraction of 384, while
production member checks dominate cold host construction.  Correct identity
may have little systems value beyond closing the gate.

**Largest unknown:** the actual h32 size of the six removed full-contender
bases and whether allocator buckets expose the reduction in pool total.

**Cheapest falsification:** the first balanced target.  A count other than 378
or raw-equivalent byte mismatch rejects the successor before any interpretation.
