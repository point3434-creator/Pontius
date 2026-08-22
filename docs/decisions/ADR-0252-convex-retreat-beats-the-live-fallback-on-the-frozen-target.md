# ADR-0252: Convex retreat beats the live fallback on the frozen target

- Status: accepted single-target strategy-quality result; fresh replication authorized
- Date: 2026-08-22
- Implements: ADR-0251
- Clean preregistration commit: `a7960be318dcada8cc60fda56f621796a05a4056`
- Result: `experiments/results/h32-one-seat-retreat-quality-v2.json`
- Result SHA-256: `126d3fbff1751902c067f96073703699165a494ba8b4fecfe0841dfc61fb157d`

## Result

Every provenance, clean-Git, inherited-config, source, target, warm-start,
path-single-visit, open-axis, row, cut, sparse-master, numerical reproduction,
exact-certificate, tolerance-separation, label-barrier, sealed-comparator,
memory, measured-ledger, conservative-ledger, immutable-emission, and finite
gate passes.

On the single known target, the independently certified factor-`0.5` retreat
reduced exact NashConv from `0.052804496976692095` to
`0.04484768632878877`, delivering exact positive value
`0.007956810647903323`.

The accepted one-step/31-block live fallback on the identical target delivered
`0.0025366954832812816`. The retreat therefore delivered
`0.005420115164622041` more exact value, or `3.13668x` the fallback value. The
strict one-raw-guard materiality gate passes by roughly six orders of
magnitude.

## Exact safety and convex diagnostics

The retreat's all-six exact certificate reports zero maximum cap violation
under the distinct `2e-11` cap allowance. Its minimum exact cap slack is
`1.4999999870674019e-9`, above the frozen `1.48e-9` interior floor and almost
exactly the half-guard prediction.

Exact retreat NashConv lies `7.472256205687255e-5` below the convex Jensen
ceiling `0.044922408890845644`. One response action flipped and the seat-4
response signature changed at the retreat, so this safety result is not merely
an unchanged-selector affine extrapolation. The independent exact oracle, not
Jensen or the master, remains the authority.

## Numerical reconstruction correction closes cleanly

The first-oracle objective, maximum cap violation, and maximum epigraph
violation reproduced ADR-0247 to respectively `4.44e-16`, `1.11e-16`, and
`5.66e-16`. All six response signatures and violating players `(4, 5)` match
exactly. The initial and second master bounds reproduced within `3.2e-15`; the
largest master primal and dual residuals were `1.11e-15` and `6.94e-18`.

As ADR-0250 predicted, the first-candidate, endpoint, and retreat policy byte
digests all differ from ADR-0247 and remain false diagnostics. No decision or
gate consumed those Booleans. The algorithmic, discrete, and Float64 witnesses
all pass, validating ADR-0251's narrow correction rather than hiding the v1
failure.

## Label barrier

The event order is exactly:

1. inputs pinned;
2. candidate frozen;
3. retreat certificate complete; and
4. sealed comparator opened.

The fallback artifact's numeric value, NashConv, and time were absent from the
v2 config and were deserialized only after the retreat certificate. Every
fallback target, depth, 31-block manifest, blueprint, candidate, policy,
certificate, deadline, payoff-span, guard, value-identity, and artifact gate
passes.

## Wall clock and memory

The measured live ledger is `9,460.421 ms`, leaving `5,539.579 ms` under the
hard street boundary. Its largest components are `2,916.881 ms` for eleven
initial rows, `1,723.961 ms` for the first oracle, `1,706.322 ms` for the
retreat oracle, and `1,653.544 ms` for the charged warm step. Both sparse
masters together cost only `12.954 ms`.

The deliberately conservative ledger remains `13,967.616 ms`, leaving
`1,032.384 ms`. Even with that denominator, retreat value per millisecond is
`2.36644x` the fallback's sealed value rate, so the strict rate gate passes.

The CuPy pool peaks at `5,661,330,944` bytes and physical free memory never
falls below `9,629,073,408` bytes. The invocation cleared all manual CUDA path
variables and reached the pinned CuPy `14.2.0`, runtime `13020`, driver `13030`,
and compute capability `120`, exercising ADR-0248's automatic DLL bootstrap.

## Decision

Accept the narrow one-target strategy-quality result. The one-seat convex
master has now produced a candidate that is independently exact-safe, restores
interior guard slack, fits the full street ledger, and materially outperforms
the accepted complete-library one-step fallback on the optimizer target.

Authorize only a separately preregistered fresh-target replication. Freeze the
fresh target or target panel before any convex candidate or label, retain the
factor `0.5`, exact two-oracle authority, distinct cap and epigraph allowances,
full conservative charge, sealed fallback comparison where available, and
immutable external blueprint. Do not tune the retreat factor from this result.

## Claims boundary

This is exact strategy-quality evidence on one previously known target. It is
not fresh transfer evidence and makes no population, multi-seat, composition,
cross-street, exploitative, deployment, or broad poker-strength claim. The
candidate was shadow-accepted and never externally emitted.
