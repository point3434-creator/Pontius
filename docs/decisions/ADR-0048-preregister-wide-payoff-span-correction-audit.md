# ADR-0048: Preregister the searched-game payoff-span correction audit

**Status:** Accepted before implementation and corrected selector inspection

**Date:** 2026-08-19

## Decision

Run one mechanical, revealed-development audit of the payoff-span mismatch
identified in ADR-0047. Replace only the normalization denominator in the
frozen selective-expansion artifact, then rerun the exact unchanged
`river-selective-width-screen-v1` procedure. Do not change an arm, feature,
threshold family, tree depth, uncertainty multiplier, group fold, timing,
quality label, or selection gate.

The frozen configuration is
`experiments/configs/river-selective-payoff-span-correction-audit-v1.json`,
SHA-256
`d2b179038972259f4d4821c3a63fac28744b13bb499630e4d658cdf411f52810`. The result target is
`experiments/results/river-selective-payoff-span-correction-audit-v1.json`.

This is a bug audit on fully revealed data. Even if the old selection outcome
changes and every old gate passes, this run cannot authorize deployment,
validation/test access, native specialization, or a neural selector. It can
only decide whether a fresh development replication is warranted.

## Frozen inputs

Require all four artifacts byte-for-byte:

1. selective-expansion source SHA-256
   `7571a8a2f3c08034b53982b4ac122106fbe3d1cc7b216d3ee4ba58cf01fdd2ff`;
2. selector rule SHA-256
   `3a8c26ee23eefaeecc87f42e23257d591734cd90abb997734e9a1761f7b385e93`;
3. original screen SHA-256
   `ee7df32361a08236603e4b2d8d3e6f26d1a209f98b86bb5ffce53fcf14be2794`;
   and
4. independent policy-delta result SHA-256
   `5c1690c4d553d615f25d14e994de4831f6842819fb6b9077e7ec9682226bb197`.

The source canonical config must remain
`3740d5a9ae9293eb71bdc3a6491cf6b5e22d40289918534755c0a414ce46e3d9`.
Require eleven board groups, 44 contexts, and 132 targets throughout.

## Frozen correction

For each target, read the pot and full action fractions from the source
artifact and compute

`searched span = pot + 2 * max(pot * maximum bet fraction, pot * maximum raise-to fraction)`.

This is the existing `MultiSizeRiverHoldem.payoff_span` definition applied to
the exact 3x2 action universe. Replace only
`targets[*].boundary_online_features.target_payoff_span` in an in-memory copy.
No corrected source artifact is written or substituted for the original
evidence.

Independently match every derived span against the actual `payoff_span` stored
by ADR-0047's regenerated wide target. Both `b3r1` and `b3r2` rows for a target
must agree. Maximum error is `1e-12`.

The old-to-corrected ratio must contain at least two distinct values. This
guards against accidentally treating the defect as one harmless global unit
conversion.

## Controls and gates

Before correction, rerun the frozen selector and reproduce these strategy
quantities from the original screen within `1e-12`:

- fixed raw and normalized reduction;
- selected candidate identifier, raw and normalized reduction, and arm counts;
- every candidate's aggregate raw and normalized reduction; and
- the complete boolean gate vector.

Exclude freshly timed tree-evaluation seconds and metrics derived from those
seconds from numerical reproduction. The strategy labels, arm decisions, and
state visits must still match.

After correction, require:

1. zero mutations outside the one declared denominator path;
2. maximum independent wide-span error at most `1e-12`;
3. maximum original strategy-quality reproduction error at most `1e-12`;
4. at least two distinct old-to-corrected ratios; and
5. identical target, group, candidate-family, fold, and feature schemas.

The corrected screen's old selection gates are reported exactly as they run,
but are not themselves correction-integrity gates. Their outcome determines
the next decision rather than whether the correction was implemented honestly.

## Frozen interpretation

- If fixed `b3r2` still wins the corrected normalized objective, or another
  candidate is selected but the unchanged joint gates fail, retain fixed full
  search and close this adaptive-width family on the current workload.
- If an adaptive specification is selected and every unchanged gate passes,
  mark ADR-0044's rejection invalid for its intended normalized objective,
  serialize the selected procedure as revealed-development only, and
  preregister a fresh group-separated development replication before
  constructing its contexts.
- In neither case may a different candidate be chosen because it appears more
  attractive in the corrected leaderboard.

## Dissent protocol

**Confidence:** very high in the mechanical correction; moderate in what the
revealed screen says about a fresh sample.

**Opposing evidence:** the narrow payoff span was a real, consistently defined
context feature and remained scale invariant. That does not make it the payoff
span of the strategy game whose NashConv was being compared.

**Largest risk:** treating a corrected held-in pass as transferable evidence
instead of only a reason to run a fresh replication.

**Cheapest falsification:** fail to match the independently regenerated wide
spans or observe any mutation outside the declared denominator field.
