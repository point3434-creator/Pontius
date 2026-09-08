# ADR-0040: Selective-expansion pilot calibrates, but does not select, branching

**Status:** Accepted

**Date:** 2026-08-19

## Decision

Retain full-action selective expansion as the correct action-width laboratory,
but do not promote a partial mask, warm-start strength, scheduler, or native
kernel from the first pilot.

At the largest tested equal-work budget, the fully expanded `b3r2` tree is the
best fixed arm. Partial expansion therefore has not yet earned specialization.
The per-instance best mask nevertheless varies across all four widths and has a
nontrivial oracle advantage. The next gate is a stronger-blueprint,
multiple-board opportunity dataset with one fixed warm regime. It must measure
whether causal pre-search or paid-probe features can recover that opportunity
without exact future labels.

## Frozen implementation boundary

ADR-0039, commit `8235c2b`, and the subsequent experiment commits establish the
following semantics before the pilot result:

- parent information sets retain the complete 3x2 action tuple;
- unexpanded nonterminal actions terminate at exact fixed-blueprint values;
- candidate behavior replaces the blueprint only at materialized information
  sets;
- all other full-game information sets remain exactly the blueprint;
- full expansion is bit-for-bit identical to ordinary full-game DCFR in the
  deterministic tests; and
- every quality label is computed in the unwrapped full 3x2 target game.

Commit `f1fa9c3` replaces the generic `repr(state)` leaf-cache key with a compact
concrete deal/history key. This removes repeated serialization of the board,
entire joint range, and game metadata from hot cutoff lookup. Commit `0eea887`
adds the fixed-warm mask oracle so mask opportunity is not inflated by also
selecting a warm-start parameter.

## Pilot evidence

The clean development artifact is
`experiments/results/river-selective-expansion-pilot-v1.json`, SHA-256
`c334724e380bca370cc691917a780f4857a41ff34fd724ff0dce2ffee996a15e`,
1,404,427 bytes. It embeds clean commit
`0eea8870a77abc61c3b429819dec3b043f18f523`.

The pilot deliberately contains only one development board group: four range
families, twelve support-preserving target ranges, 48 target/mask structures,
and 720 candidate records. It is parameter calibration, not transfer evidence.
No validation or test board was materialized.

Every structural gate passes. Relative to full `b3r2`, the mean deterministic
tree-state fractions are:

| Mask | Tree states | Materialized information sets | Mean exact leaves |
|---|---:|---:|---:|
| `b1r1` | 38.081% | 30% | 42.75 |
| `b2r1` | 58.721% | 50% | 42.75 |
| `b3r1` | 79.360% | 70% | 42.75 |
| `b3r2` | 100% | 100% | 0 |

The equal leaf counts in the partial masks are structural, not suspicious.
Each newly expanded opening-bet branch removes one cutoff but exposes one
unexpanded raise cutoff per deal.

## Fixed-arm result

At warm pseudo-regret mass `0.1 * payoff_span` and a budget equal to sixteen
full-tree iterations:

| Mask | Mean full-game NashConv reduction | Reduction / million state visits | Improve | Harm |
|---|---:|---:|---:|---:|
| `b1r1` | -0.085774 | -6.4730 | 50.00% | 50.00% |
| `b2r1` | -0.097907 | -7.4536 | 50.00% | 50.00% |
| `b3r1` | +0.004358 | +0.3314 | 58.33% | 41.67% |
| `b3r2` | +0.104489 | +7.8824 | 66.67% | 33.33% |

Thus the second raise-to size earns its cost on aggregate in this one-board
pilot. Removing it is not a fixed quality/work win. Blind full expansion is
still unsafe: four of twelve target instances worsen, including correlated and
balanced cases. No exact-label no-op gate is available online.

The smallest tested warm multiplier, `0.01 * payoff_span`, permits catastrophic
early policy movement; the worst candidate increases NashConv by `19.1732`.
The largest multiplier, `1.0 * payoff_span`, is more inert but does not produce
positive aggregate reduction at the largest budget. This reproduces the older
lesson that fixed raw pseudo-regret mass is not a transferable safety device.

## Adaptive opportunity

Holding warm strength and the sixteen-iteration-equivalent work budget fixed,
the best mask wins the following number of the twelve instances:

- `b1r1`: 1;
- `b2r1`: 2;
- `b3r1`: 4; and
- `b3r2`: 5.

The raw best-mask oracle totals `1.50353` NashConv reduction versus `1.25387`
for always-full expansion. Adding exact-label no-op options raises those totals
to `1.86440` and `1.67320`, respectively. The mask-plus-no-op oracle is therefore
`0.19121`, or 11.43%, above the full-tree-plus-no-op oracle. It retains the
blueprint in two instances versus four for the full-tree oracle.

This is a ceiling only. It uses full-game future labels and supplies neither a
deployable stopping rule nor evidence that available features can rank masks.

## Timing interpretation

Compact cache keys lower partial-tree Python time materially, but at equal
state work the reference wrappers remain slower than the straight full tree.
At the largest `0.1`-warm budget, mean hot times are approximately 101.01,
100.32, 99.65, and 93.49 ms from `b1r1` through `b3r2`. Dispatch, wrapper, and
dictionary leaf lookup dominate the saved Python recursion. Exact cold leaf
construction adds only about 0.73-1.55 ms here.

These figures reject a Python latency win. They do not predict a branch-lane
C++ crossover, because all arms are deliberately given nearly equal counted
state work and the reference wrapper has no native leaf opcode. State counts
remain the stable development cost; native wall time must later be measured.

## Blueprint-strength correction

The fixed 512-iteration source blueprint is uneven. Source NashConv is below
`7.47e-4` in three families but `0.0158651` in the correlated family. A
post-pilot calibration on that same revealed correlated context reaches
`0.00252277`, `0.000868899`, and `0.000292878` at 1,024, 2,048, and 4,096 DCFR
iterations. These are development diagnostics, not fresh evidence.

The next matrix must use an explicit source-NashConv strength threshold at
declared checkpoints, with a fixed maximum, rather than calling one iteration
count “strong” across all range families.

## Next gate

Before native action-lane work:

1. freeze multiple unseen development board groups;
2. construct each full 3x2 source blueprint to the same declared exact quality
   threshold;
3. fix one normalized warm regime and remove warm-strength selection from the
   mask question;
4. record mask-independent range, blueprint, cache-delta, and paid-probe
   features without exposing future full-game labels;
5. measure fixed masks, the exact best-mask/no-op ceiling, and a transparent
   causal heuristic at equal state work; and
6. require a partial or adaptive policy to lie on the held-out development
   quality/work frontier before specializing the C++ layout.

## Dissent protocol

**Confidence:** high in the selective-expansion semantics and measured work
fractions; moderate that mask opportunity is real in this board; low that its
11.43% oracle uplift transfers or is predictable.

**Opposing evidence:** the best fixed arm is full expansion, all blind arms harm
some targets, the source blueprint is uneven, and the pilot has one board.

**Cheapest falsification:** repeat the frozen semantics on group-separated
development boards with uniformly strong blueprints. If the fixed-warm
best-mask/no-op ceiling collapses or no causal probe beats always-full plus a
no-op fallback, defer adaptive branching and optimize the full lattice only
after it survives earlier-street and multiplayer tests.

