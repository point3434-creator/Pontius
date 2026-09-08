# ADR-0047: Accept exact policy deltas, reject sparsity as the main mechanism

**Status:** Accepted

**Date:** 2026-08-19

## Decision

Accept the policy-parameterized Float64 dependency tape as an exact reference
and reusable evaluator. Do not characterize realistic selective candidates as
sparse. Automatic execution should normally choose the dense flat pass on this
workload, while retaining sparse execution for the minority of genuinely local
changes.

Exact accept/no-op is now a demonstrated heads-up river mechanism, not merely a
future-label diagnostic. For one candidate with no reusable compilation,
however, the ordinary exact evaluator remains marginally more efficient than
compiling and updating the tape. The tape advances only where its compilation
is already available or shared by at least two candidate evaluations.

This does not authorize a six-player safety claim, a live deployment rule, or a
return to the rejected width selector.

## Frozen evidence

ADR-0046 was committed as `264d68a` before implementation. The implementation
and all 276 automated tests were committed as
`d430f4abe1db8a5dc5efb2d3254e1fc32fa0fcd9` before the real matrix ran. The
tests passed in 49.573 seconds.

The result artifact is
`experiments/results/policy-delta-recertification-development-v1.json`, SHA-256
`5c1690c4d553d615f25d14e994de4831f6842819fb6b9077e7ec9682226bb197`.
It contains 264 candidates over the frozen eleven groups, 44 contexts, and 132
range targets. Its canonical config SHA-256 is
`84099c044a7824f4bd848b699580027f36997aa2754395fb114103c62c3d6c29`.

Every regenerated source and candidate label matches the earlier artifact
exactly. Maximum error across utilities, best-response values, deviation
gains, NashConv, and exploitability is `8.88178e-15`. There are zero
best-response action mismatches, zero accept/no-op mismatches, and zero
source-relative order or replay failures. All dependencies remain topological.

## Quality per millisecond

The primary full `b3r2` arm has 132 candidates. The conservative payoff-scaled
gate accepts 96. Payoff-normalized signed reduction rises from `0.16165609`
under blind deployment to `0.21483794` after exact rejection.

Fresh primary costs are:

- candidate construction and solving: `24.41999` seconds;
- ordinary full candidate evaluation: `1.578454` seconds;
- hot policy-delta evaluation: `0.264676` seconds; and
- one compilation per target: `1.485942` seconds.

Thus the hot tape is `5.96372x` faster than ordinary evaluation. Normalized
quality rates are `6.61983e-6` per millisecond for blind full search,
`8.26349e-6` for the ordinary exact gate, `8.70330e-6` for the hot tape gate,
and `8.20913e-6` for the compile-charged tape gate.

The hot tape improves on blind search by `31.4732%` and on the ordinary exact
gate by `5.32224%`. Compilation charged once per candidate still beats blind
search by `24.0083%`, so the preregistered gate passes, but it trails the much
simpler ordinary exact gate by `0.657853%`. Across these targets, sharing one
compile over two equally distributed candidate evaluations would make the
evaluation stage about `1.57x` faster than evaluating both independently.

## The sparsity hypothesis mostly fails

For full `b3r2`, the median candidate changes 70% of information sets and the
mean changed policy-entry fraction is 67.18%. The mean dirty-node fraction is
72.82%, the median is 81.42%, and automatic execution chooses sparse mode on
only 16.67% of records.

Near-full `b3r1` is somewhat more local but still mostly dense: median changed
information-set fraction 48.75%, mean changed entry fraction 53.27%, mean dirty
fraction 63.01%, median dirty fraction 66.63%, and automatic sparse execution
on 19.70% of records.

The speedup therefore comes primarily from compiled flat evaluation and reuse,
not from a small affected cone. A native kernel should optimize the dense
policy pass first and retain sparse invalidation as a secondary lane.

## Payoff-span anomaly discovered during interpretation

The new runner normalizes by the actual searched
`MultiSizeRiverHoldem.payoff_span`. ADR-0044's selector instead reads
`target_payoff_span` from the narrow range-context feature record. Those two
denominators differ by factors from `1.25` to `3.33333` across the 132 targets,
not by one harmless global constant.

Raw labels and all policy-delta conclusions above are unaffected. Positive
payoff-rescaling invariance in ADR-0045 also remains true, but it could not
detect selection of the wrong scale definition because both definitions scale
linearly. Consequently, ADR-0044's specific normalized-quality comparison and
ADR-0045's claim that this comparison was fully validated are no longer strong
evidence until a frozen denominator-correction audit is run.

This observation does not retroactively select an adaptive tree. The data are
revealed, and changing the denominator can change model selection. Fixed
`b3r2` remains the incumbent until the same frozen screen is recomputed as an
explicit bug diagnostic and, if its verdict changes, replicated on fresh
development groups.

## Next gate

First freeze the mechanical payoff-span correction before recomputing any
selector outcome. Derive the searched span from the full action universe,
verify it against independently regenerated wide games, and report both old
and corrected screens without retuning any arm, feature, tree, or gate.

After that audit, measure evaluator reuse at one, two, and several candidates
per compiled target. A native SoA policy kernel is justified only after the
corrected measurement objective is stable and reuse is representative of the
intended runtime.

## Dissent protocol

**Confidence:** very high in exact identity; high in the observed Python timing
rank; high that policy cones are usually dense here; low in six-player transfer.

**Opposing evidence:** a native sparse kernel may have a different crossover,
and compilation may be precomputed during otherwise idle time. Neither changes
the measured fact that current candidates touch most of this exact circuit.

**Largest unknown:** whether realistic runtime can reuse a target-specific
compiled evaluator often enough to retain the hot advantage.

**Cheapest falsification:** charge one fresh compilation for every single
candidate. Under that workload the tape already loses slightly to ordinary
exact evaluation, so no native specialization should be justified by hot
numbers alone.
