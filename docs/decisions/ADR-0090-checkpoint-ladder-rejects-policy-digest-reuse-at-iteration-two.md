# ADR-0090: Checkpoint ladder rejects policy-digest reuse at iteration two

**Status:** Frozen ADR-0089 execution rejected before new quality points;
restart serializer retained, source-reuse contract corrected in successor

**Date:** 2026-08-20

## Result

The frozen ADR-0089 audit ran from clean commit
`0d33c53` and stopped before iteration two completed its source-quality reuse
step. No canonical result artifact was written.

The rejection is valid. `_copied_quality_row` required the live policy digest
to equal the immutable ADR-0087 policy digest before reusing its NashConv row.
The live iteration-two current policy did not match byte-for-byte, so the audit
refused to attach a value measured on another literal policy.

Do not relax the frozen condition or label this a pass. The experiment never
reached iterations 4, 8, 16, or 32.

## Localization

A post-rejection diagnostic reran the balanced h32 trajectory under the same
pinned environment and compared its policies with ADR-0085.

Iteration one is exactly reproducible:

- current digest:
  `925c99980ca91d5a250332c2870540c9eed9bf18fbdd32da8920771c82a1fbb2`;
- average digest:
  `7e60a4a86ea63711a6a164f9ef56d63aa0ab3e15d41c546105f9c9e6601913de`;
- maximum current or average probability error: `0.0`; and
- differing information rows: zero.

At iteration two:

- the average remains byte-identical, digest
  `fbd649d82a3a5f35c5c4477ac828c7bbdcd2158d73b1332f8d580db9aff763d1`;
- the live current digest is
  `8048055923257bc3948980ed9c3ff45832634962aaa732a3de852cfa607baa17`;
- the frozen source current digest is
  `69855dd1c4efecf64c5c6d1214814dc1e29a23b33737cdce0d1f85d82001fdce`;
- maximum probability difference is `2.94e-14`;
- 796 hand-action entries in 446 information rows differ bitwise;
- mean policy TV is `7.26e-17`;
- 203 entries differ by more than `1e-15`; and
- no entry differs by more than `1e-12`.

The difference is numerically tiny and almost certainly immaterial to the
strategy metric. That does not make the old NashConv row a literal evaluation
of the live policy. Reusing it would violate the frozen identity semantics.

## Why the average matches while current does not

The iteration-two average accumulates the uniform first strategy and the
iteration-one current strategy. Both are byte-identical across the runs, so the
average is byte-identical.

The iteration-two current is regret matching over the hidden accumulator state
after two GPU sweeps. An identical normalized policy after sweep one does not
imply identical regret magnitudes: positive regrets can differ by tiny common
or near-common scales while producing the same normalized distribution. The
next regret update exposes those hidden differences.

This distinction is the architectural lesson:

- a policy digest certifies one behavioral profile;
- it does not certify a resumable CFR state; and
- only the full regret/strategy-sum state digest introduced by ADR-0089 can
  certify trajectory continuation.

The restart format is therefore strengthened by this failure, not weakened.

## Decision

1. Reject ADR-0089 as executed; no later checkpoint result exists.
2. Retain the exact h4 warm/cold serializer tests and frozen state format.
3. Retain identity reuse at iteration one for both policies and at iteration
   two for the average, where live digests match exactly.
4. Do not reuse ADR-0087's iteration-two current quality row.
5. In the successor, evaluate the live iteration-two current policy directly.
   Do not introduce a fitted policy-distance threshold or pretend that
   `2.94e-14` is universally harmless.
6. Continue the live solver state—not ADR-0085's unrestartable policy source—
   through the later ladder.

## Successor correction

Freeze an explicit per-policy measurement matrix:

| Iteration | Current quality | Average quality |
|---:|---|---|
| 1 | reuse only on exact digest | reuse only on exact digest |
| 2 | live evaluation | reuse only on exact digest |
| 4 | live evaluation | live evaluation |
| 8 | live evaluation | live evaluation |
| 16 | live evaluation | live evaluation |
| 32 | live evaluation | live evaluation |

This adds one six-seat evaluation per family, roughly 21-30 seconds, and
removes all tolerance judgment from the reuse decision. The one-hour wall gate
has ample headroom.

The successor should report the iteration-two current distance to ADR-0085 as
a diagnostic, but it may not use that distance to import the old value.

## Limitations

- The diagnostic establishes policy distance, not the exact internal source
  regret-state difference; ADR-0085 did not serialize that state.
- The precise source of the tiny state difference—GPU reduction history,
  allocation/warmup state, or another deterministic execution detail—is not
  yet isolated.
- No new strategy-quality point was revealed, so the iteration-4+ ladder
  remains held out for the successor.

## Dissent protocol

**Confidence:** very high in the localization and policy distances; very high
that exact reuse correctly rejected; high that live evaluation is the cleanest
correction.

**Opposing evidence:** the policy difference is far below any practical action
or value tolerance, so strict identity costs an extra evaluation. That cost is
small relative to the risk of silently relabeling a measured object.

**Largest risk:** replacing exact reuse with an arbitrary closeness rule that
later admits blocker-sensitive policy differences. The successor deliberately
avoids such a rule.

**Cheapest falsification:** live iteration-two current NashConv. It should
agree numerically with ADR-0087 if the `2.94e-14` policy difference is harmless,
but the comparison remains a diagnostic after both values are independently
measured.
