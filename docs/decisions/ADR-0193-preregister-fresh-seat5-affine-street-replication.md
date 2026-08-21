# ADR-0193: Preregister a fresh seat-5 affine street replication

- Status: accepted preregistration
- Date: 2026-08-21
- Depends on: ADR-0179, ADR-0190, ADR-0192
- Config: `experiments/configs/h32-fresh-selector-stable-affine-street-seat5-v1.json`

## Question

Does ADR-0192's online-feasible mechanism transfer unchanged to the other
order extreme, acting seat 5, on a second fresh four-context panel?

This is a direct replication of the live core, not a new selector. The acting
seat and fresh target beliefs change; the warm step, regret vertex, affine
proof, scale rule, deadline guards, causal teacher boundary, and fallback do
not.

## Fresh target panel

Use the four remaining source-panel contexts whose seat-4 blocker shifts have
not appeared in the sealed repository history:

| Target | Selected seat-4 hand | Frozen target SHA-256 |
|---|---|---|
| panel 1 blocker-heavy | `2h 3c` | `9cb9f6c30990baab33c710ce5bbef634cd903d5dd11346b26b7037b03d1d5953` |
| panel 2 balanced | `7s 9s` | `4bf33595af8b344e01b534ea12ad5619fac2e307f06d4e1e1be55ca6d7f4c0de` |
| panel 3 balanced | `6s Kh` | `add4941c6ee083319afcbfbe8df2a02afb672c652b46236f0e265cbc4fcf7cac` |
| panel 3 blocker-heavy | `2s 8h` | `2df7b14b451769607ed037c0a7cd5ed77f7253c1382d40ac798078690ab4a2db` |

The construction doubles the likelihood of the seat-4 hand chosen by maximum
opponent-axis card overlap, then strength, then smallest canonical hand. Target
and descriptor digests must be absent from
`d59b8577220229e6b49c9b904a57a8c1787b2cb5`, the sealed ADR-0192 result commit.
Panel 1 balanced and panel 2 blocker-heavy are excluded because ADR-0169
already labeled their seat-4 shifts.

## Sole mechanism substitution

Treat ADR-0191's additive runner as immutable. Reuse its complete preparation,
clock, one-step DCFR, all-block construction, affine envelope, live emission,
post-emission teacher, resource accounting, and gates. A hash-bound successor
substitutes only:

- target construction seat `0 -> 4` and the frozen four-target panel; and
- acting block `0 -> 5`.

The fixed candidate is acting seat 5's instantaneous-regret vertex at its
deterministic exact public node. Retain the half-radius and geometric grid,
`1,000 ms` post-step candidate/proof guard, `500 ms` post-construction affine
guard, `14,000 ms` candidate-ready cutoff, and `1,000 ms` emission reserve.

Do not add a material-value threshold from ADR-0192, even though its values
spanned 565x. Do not select between seats 0 and 5, inspect another block's
regret, or introduce a rescue direction.

## Causal teachers and gates

Freeze simulated emission before the old exact verifier starts. If a start
guard denies live work, close with the preloaded blueprint and perform the
affine proof and exact checks only as post-ledger diagnostics. Teachers may
reject the run but cannot change the live outcome.

Inherit every ADR-0191 outcome-neutral gate byte-for-byte: four targets and
steps, four fixed blocks, 24 affine rows, four fixed witnesses, fresh-history
absence, numerical warm identity, exact one-node scope, `2e-11` intercept and
`1e-9` teacher error ceilings, zero response flips, causal emission, hard
15-second ledgers, 60-second component ceilings, 12 GB pool ceiling, 1 GB
physical-free floor, finite accounting, and the 1,800-second total ceiling.

Do not gate on construction or proof start count, non-blueprint emission count,
scale, value, target outcome, guard margin, or agreement with ADR-0192's four-
of-four result.

## Frozen artifacts

- config SHA-256:
  `f0b95471a91c68015b785ce0876afd81cdd3617f21229030540972a797442fb0`;
- additive successor SHA-256:
  `9b69918ff4a367d6a37d0189e0223467cad5209ab8f3685e1fd29c91a90ca3f3`;
- mutation-control SHA-256:
  `0828e32606a98c01f3827d754d1b725da337ebe3d6e9bc7db75757b8e811ae20`;
- result target:
  `experiments/results/h32-fresh-selector-stable-affine-street-seat5-v1.json`.

The 11 focused live-core, seat-substitution, freshness, and affine controls
pass. No fresh seat-4 target policy step or quality teacher has run.

## Decision rule

Commit the successor wrapper, config, controls, and this ADR before any fresh
seat-4 target policy step. Execute once from that clean commit. A pass is only
four-context prospective evidence for fixed acting seat 5. A deadline or
exactness failure stops the line for runtime repair; sparse or microscopic
value is recorded without retuning.
