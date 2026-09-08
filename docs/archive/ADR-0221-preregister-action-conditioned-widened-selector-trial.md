# ADR-0221: Preregister the action-conditioned widened selector trial

- Status: accepted preregistration
- Date: 2026-08-21
- Follows: ADR-0220
- Experiment: `experiments/configs/h32-action-conditioned-widened-selector-v1.json`

## Context

ADR-0220 froze 12 exact blueprint-action posteriors spanning all three boards,
both source range families, and every observed bettor twice. Acting-seat
marginal TV is `0.567` to `0.723`, materially wider than the synthetic shifts
used to develop the selector.

Retained-label ADR-0206 identified the exact Tier-B objective-slope times
cap-radius composite, but rejected Tier A as a filter. ADR-0212 then made all
six retained blocks fit the 15-second ledger. The fresh panel must now test the
composite where the candidate library is wide enough for selection to bind,
without adapting either the library or labels after seeing results.

## Frozen candidate corpus

For each of the 12 target beliefs, reconstruct the immutable average-64 source
blueprint and perform exactly one device-fold DCFR warm step. Partition every
changed information set by exact `(acting seat, public history)`. Every
nonempty block receives exactly one regret-vertex endpoint. No soft or
best-response-vertex family is included.

The library is ordered without feature or label access:

1. descendants of the complete observed checks-then-bet prefix;
2. increasing public-action-tree edit distance from that prefix;
3. acting seats in order `0, 5, 1, 4, 2, 3`; and
4. acting seat and lexicographic public history as final tie-breaks.

All blocks remain in the scientific corpus. The old one-block-per-seat
selection is tagged as a six-block comparison subset only; it cannot remove a
new block.

## Frozen feature and clock phase

Compute the exact zero-contraction own row and five charged opponent
BR-conditioned rows for every block. The opponent rows use the promoted
device-fold scalar path. ADR-0210's null batching result forbids assuming a
cross-candidate packing gain. Tier A is retained only as an identity
diagnostic and may not filter candidates.

The live simulation takes the first structurally scheduled `K` blocks, ranks
them by the Tier-B slope-times-cap-radius composite, and spends one Tier-C
affine envelope on the winner. `K` is derived independently per target as:

`floor((15000 ms - warm step - 1000 ms reserve - maximum one-winner envelope) / maximum complete per-candidate Tier-B cost)`.

The maximum complete candidate cost includes endpoint construction, the own
row, and all five opponent rows. `K` is capped by library width. Failure to
produce a Tier-C scale, `K = 0`, or a missed deadline means immutable-blueprint
fallback.

The audit computes the full feature matrix off-clock to measure transfer. That
does not authorize the live simulation to inspect more than its structurally
first `K` rows. Report full-library composite performance separately from the
clock-priced live portfolio.

## Frozen label barrier and exact teacher

Complete all 12 feature matrices, structural schedules, affine envelopes, and
capacity rows while every strategy label is null. Only then open the teacher
phase.

For each candidate with a selected affine-envelope scale, interpolate once
from the immutable blueprint and run one independent incremental exact
certificate. The label is the positive exact NashConv reduction at that exact
scale if the certificate is complete, otherwise zero. A candidate for which
the affine envelope proposes no scale receives zero realized B-to-C value and
does not trigger a direct query.

There is no adaptive scale search. This label measures the value actually
delivered by the frozen B-to-C path and can therefore expose selector-window
or affine-boundary failures. It is a lower bound tied to this path, not global
attainable value.

## Frozen reporting

Report each target before pooled summaries:

- candidate count, measured warm-step time, conservative `K`, and whether the
  widened library binds;
- full-library composite rank/capture and the clock-priced live capture;
- exact random-at-`K` floor and clairvoyant-at-`K` ceiling;
- common-six oracle value and full-library lift over it; and
- affine identity, certificate, memory, and wall-clock diagnostics.

No low-value or inconvenient target may be removed. No selector, schedule,
guard, numerical floor, reserve, direction family, or teacher scale may be
changed after the clean preregistration commit.

## Gates and scope

Use ADR-0179 numerical identity: `2e-11` affine/intercept ceilings and the
existing `1e-12`/`1e-13` warm-policy ceilings. Require all 12 source, target,
blueprint, block-partition, feature-barrier, independent-teacher, memory, and
immutable-emission gates. The experiment emits only the blueprint and may run
for at most three hours off-clock.

These targets condition the complete river-game ranges on observed public
actions but do not compile continuation-root subgames. The result can identify
fresh opportunity magnitude and selector transfer under range conditioning;
it cannot establish continual-resolving behavior, deployed latency,
population quality, composition, or broad strategy quality. Make no strategy-
quality claim from this preregistration.
