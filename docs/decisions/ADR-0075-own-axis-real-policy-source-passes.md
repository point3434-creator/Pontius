# ADR-0075: Canonical own-axis real-policy source passes

**Status:** Accepted as the immutable policy source for the representation successor

**Date:** 2026-08-19

## Result

The preregistered ADR-0074 source run passed every frozen gate from clean commit
`40c42052a2d2a87e58646747cab3091f02987e53`.

The canonical artifact is
`experiments/results/real-policy-source-v1.json`. Its SHA-256 is
`cdcae48dcca5fd1447fd5ad33426a4b20f04e098c88897d8f0f6eddb797ef36e`
and its size is 13,370,654 bytes. Downstream representation work must load this
object and verify that digest; it may not regenerate or replace the policies.

The artifact contains four exact source geometries, 22 DCFR-average checkpoint
profiles, and 24 all-seat literal unilateral-response profiles, for 46 complete
policy tables.

## Identity gates

All seven frozen gates pass:

- independent replay has zero probability error and zero policy-digest
  mismatches;
- every policy/action schema is exact;
- maximum literal response target-value error is
  `1.0880185641326534e-14`;
- maximum source-profile zero-sum residual is
  `1.9595436384634013e-14`; and
- all checkpoint and all-seat response objects are present.

The complete run took 125.572 seconds. Source layout compilation took 0.154-
8.857 seconds per geometry. Primary solve time was 6.273-23.453 seconds per
geometry; deterministic replay intentionally paid that solver bill a second
time.

## Strategy metadata, not a source gate

Finite DCFR quality improved monotonically on all four source games:

| Geometry | Uniform NashConv | Checkpoint 16 | Last checkpoint | Last normalized by span |
|---|---:|---:|---:|---:|
| h4 balanced | 14.3775 | 1.34474 | 0.0147662 at 256 | 0.04922% |
| h4 blocker-heavy | 14.2315 | 1.42768 | 0.0119004 at 256 | 0.03967% |
| h7 balanced | 14.3599 | 1.99332 | 0.149123 at 64 | 0.49708% |
| h7 blocker-heavy | 13.6931 | 1.99310 | 0.124190 at 64 | 0.41397% |

These values describe only the selected finite six-player river games. They do
not establish multiplayer convergence, full-range quality, or a blueprint
checkpoint choice.

Checkpoint one is bit-identical to checkpoint zero's uniform policy. This is
the correct alternating-average behavior: each seat's first average
contribution is collected before that seat receives its first regret update.
The first nonuniform object is checkpoint four.

The largest consecutive mean information-set policy changes occur from
checkpoint 4 to 16: `0.18608`, `0.19758`, `0.21334`, and `0.17650` across the
four geometries. Checkpoint 16 to 64 remains material at `0.07673-0.12300`.
These measured deltas become the real candidate-size axis for the clean-fringe
reader.

## Representation-relevant observation

No average checkpoint contains an exactly pure information set, but the late
policies are not low-cardinality textures. The last h4 averages have 744 and
757 distinct action distributions across roughly 768 information sets; the
last h7 averages have 1,329 and 1,318 across roughly 1,344. Mean entropy falls
from `ln(2)` at uniform to `0.3187-0.3543` on the h7 checkpoint-64 profiles.

This makes the next rank screen informative. The policies are smooth averages
in the provenance sense, yet heterogeneous across almost every hand/history.
They could compose substantially better than hashed-dense because poker
structure aligns the variation, or nearly as badly because the public folds
see a generic hand tensor. Neither conclusion is assumed.

Each unilateral response makes exactly one sixth of the global information
sets pure, confirming that the splice changes only its declared seat. Response
profiles remain explicit-state customers and receive no compression gate.

## Decision

Accept the artifact as the sole real-policy input for the successor. Freeze the
representation/read-path audit against its full SHA-256. Retain uniform,
hashed-dense, and hashed-pure controls on identical geometries. Report rank
versus checkpoint before interpreting any speed result.

The successor must give clean-fringe reads, recompose-then-contract, and the
flat compatible-deal evaluator the same compile/marginal/break-even accounting.
No small-axis speed win authorizes a 32-hand runtime lift.

## Limitations

- The object contains selected four/seven-hand axes, not all 1,081 hole-card
  combinations.
- Six-player DCFR does not inherit two-player exploitability convergence.
- Exact all-seat BR evaluation is an offline source diagnostic, not an online
  decision bill.
- The artifact reveals policy quality and TV but no TT rank or candidate-reader
  performance.
