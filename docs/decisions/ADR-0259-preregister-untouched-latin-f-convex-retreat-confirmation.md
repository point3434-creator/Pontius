# ADR-0259: Preregister untouched Latin-F convex-retreat confirmation

- Status: accepted preregistration before any Latin-F warm step, candidate, or strategy label
- Date: 2026-08-22
- Follows: ADR-0258
- Config: `experiments/configs/h32-latin-f-convex-retreat-confirmation-v1.json`
- Config SHA-256: `958a8756cfa68e2995a6dd325dd9a099f1960dab6ea6f7c1ee654459b0689810`
- Runner SHA-256: `6e71089bcc668e94d64d9174b7b8cda74cef223a434ebc103d58f4f2dbdbacf8`
- Control SHA-256: `2e1f84eb32215a547fc55c299309539e393f549db572e448c3b69e79c1117ab7`

## Question

Does ADR-0258's all-six material-value breadth result confirm on the six
untouched Latin-F action-conditioned posteriors under the identical one-seat
master, half-retreat, exact certificate, and complete 15-second ledger?

This is the confirmatory branch authorized before Latin-E labels. It tests the
same engineering breadth threshold on a fully untouched panel. It does not
estimate a population rate, compare against a fresh regret-vertex fallback, or
authorize deployment by itself.

## Frozen confirmation panel

Use all six Latin-F rows from ADR-0254 in manifest order. They are disjoint from
Latin-E and contain one target per source context, observed bettor, and acting
player, with three balanced and three blocker-heavy ranges. Acting player
remains the position-equivariant last responder `(bettor - 1) mod 6`.

No Latin-E value, cap slack, timing, cut count, response signature, TV,
opportunity measurement, source, family, or position may select, reorder, tune,
or omit a Latin-F target. The config contains no Latin-E pooled-value threshold
and no expected Latin-F value. Latin-E is pinned only as the parent that
authorized this branch.

Every Latin-F final retreat label is a first evaluation. Run no pilot, dry-run
oracle, target-specific calibration, or fallback comparator before the frozen
campaign.

## Unchanged algorithm

The confirmation config is a hash-pinned overlay on ADR-0257's complete v2
config. Preserve exactly:

- one charged resident DCFR warm step per target;
- the path-single-visit behavioral shortcut and mandatory topology gate;
- 512 acting-seat information sets, 1,024 policy variables, and six epigraphs;
- six profile rows, the exact acting-seat invariance row, and five opponent
  source-response rows;
- source restricted master, one exact construction oracle, every new opponent
  response facet above `1e-9`, at most one multi-cut resolve, and fixed
  factor-`0.5` blueprint retreat;
- resident-row identity ceiling `2e-11` and resident epigraph-residual ceiling
  `1e-8`;
- LP/projection tolerance `1e-10`, cap allowance `2e-11`, epigraph allowance
  `1e-9`, and quality allowance `1e-10`;
- normalized guard `1e-10` and raw guard `3e-9` derived only from
  `layout.game.payoff_span`; and
- one independent exact all-seat retreat certificate as the sole final safety
  and quality authority.

Do not add another cut round, change the factor, use a Latin-E endpoint as a
warm start, or introduce an endpoint/global-optimality claim.

## Campaign-wide barrier and reconstruction

Construct, check, and freeze all six Latin-F candidates before opening any
final retreat label. Each construction must report zero final strategy labels.
Only after the campaign event `all_candidates_frozen` may certificates run in
the original manifest order.

Release device contexts between candidates. Before each final oracle,
reconstruct the pinned context and require exact checkpoint, posterior,
blueprint, retreat-policy, payoff-span, source-gain, and cap identities. Report
and gate reconstruction wall time separately; exclude it from live work because
the production-shaped path retains its resident context. Charge the entire
final oracle to the live ledger.

## Exact acceptance, timing, and memory

For each target, shadow-accept only when the final independent oracle proves:

1. every exact deviation gain is within its immutable-blueprint cap under the
   separate `2e-11` allowance;
2. exact NashConv improves by more than `1e-10`;
3. minimum cap slack is at least `1.48e-9`; and
4. measured and effective conservative schedules both fit 15,000 ms.

The live ledger remains warm step + eleven initial passes + master solve(s) +
first exact oracle + new cut extraction + final exact oracle + the 50-ms
retreat/envelope floor + 1,000-ms emission reserve. Effective conservative time
is at least `13,967.6157 ms`. Preserve the 12-GB GPU-pool ceiling, 1-GB physical-
free floor, 60-second major-phase ceilings, 120-second setup/reconstruction
ceilings, and 1,200-second total campaign ceiling.

A safe but late, nonpositive, or insufficiently interior result is a scientific
rejection for that target and emits the immutable blueprint. Every actual
external policy remains the blueprint even when its shadow candidate passes.

## Confirmation rule

Apply the same breadth branch that promoted Latin-F, without adjustment. A
target is material only if it shadow-accepts and exact value is strictly above
`0.001`. Confirm the Latin-E breadth result only if:

- at least four of six Latin-F targets are material;
- both balanced and blocker-heavy ranges occur in the material set; and
- every Latin-F target fits both measured and effective conservative ledgers.

Do not gate on Latin-F pooled value relative to Latin-E, sign concordance by
source, or any post-hoc distributional statistic. Those may be reported only as
descriptive measurements.

If the branch passes, accept combined Latin-E/F breadth evidence and authorize
only a separately preregistered prospective live-shadow integration test with
the same immutable fallback. If it fails cleanly, retain Latin-E as positive
development evidence but reject that integration step at this design point.
Process-gate failure rejects the confirmation execution rather than deciding
the scientific branch.

## Claims boundary

A pass may establish replication of material exact safe shadow value across
the two fixed six-target Latin panels. It still cannot establish a population
success rate, fresh fallback dominance, full-game or coalition safety,
multi-seat composition, cross-street reuse, global one-seat optimality,
deployment strength, exploitation quality, or broad poker strength.

## Decision

Commit the runner, overlay config, controls, this ADR, roadmap, and generated
status from one clean tree. Run the complete CPU suite, then invoke the frozen
Latin-F campaign once with automated CUDA DLL discovery. Audit and seal the
confirmation or rejection branch before any live-shadow integration work.
