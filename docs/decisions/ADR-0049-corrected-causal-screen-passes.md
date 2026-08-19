# ADR-0049: Corrected causal computation gate passes; require fresh replication

**Status:** Accepted

**Date:** 2026-08-19

## Decision

Invalidate ADR-0044's normalized rejection for its intended searched-game
objective. Freeze the corrected screen winner as a revealed-development
candidate procedure, not a deployable rule:

```text
if range_delta_changed_deal_fraction <= 0.14835164835164835:
    no_op
else:
    search full b3r2
```

The frozen specification is `delta_only__depth_1__risk_1`. It uses the five
preregistered range-delta geometry features during fitting, but the fitted tree
uses only changed-deal fraction. It chooses no-op or full search and never
chooses near-full `b3r1`; this is evidence for a causal computation gate, not
for dynamic bet-size pruning.

Preregister a fresh, larger, group-separated development replication before
constructing any new context. Fixed `b3r2` remains the runtime incumbent until
that replication passes unchanged.

## Frozen evidence

ADR-0048 was committed before implementation. A 65-character rule-hash
transcription was rejected by the first unit test and corrected in `d16b779`
before the audit ran. The audit implementation was committed as
`f65edfff1b51dbe86d7be96e8fc44e79edee20e6`; all 281 tests passed in 49.584
seconds before outcome inspection.

The result artifact is
`experiments/results/river-selective-payoff-span-correction-audit-v1.json`,
SHA-256
`cb10f19d1833721850b9e3fb79b1fc41a66944e47f472bdd1df1e99ad1ac977b`.
Its canonical config SHA-256 is
`aa05259c0bee065d6f04a856a8c5efe1afdc7d9c36c041008475f329d36f0202`.

The audit reproduces the original strategy-quality screen with zero numerical
error and identical structure. Exactly 132 declared payoff-span fields change;
zero other fields change. Derived wide spans match ADR-0047's independently
instantiated games exactly. Corrected-to-old ratios are `1.25`, `1.66667`, `2`,
and `3.33333`, confirming a nonuniform objective distortion.

## Corrected result

The corrected fixed-full control has normalized reduction `0.16165609`, raw
reduction `8.81632360`, 3,488,448 state visits, `24.754029` seconds, and maximum
target harm `2.41898350`.

Grouped out-of-fold selection chooses the fixed threshold rule above. It
selects full search 69 times and no-op 63 times. It achieves:

- normalized reduction `0.17696426`, a `9.46959%` increase over fixed full;
- raw reduction `12.45860315`, a `41.3129%` increase;
- raw reduction/ms `9.70702e-4`, a `172.549%` increase;
- 1,762,048 state visits, `49.4891%` fewer;
- `12.834629` charged seconds, `48.1514%` fewer;
- maximum target harm `0.19660560`, `91.8724%` lower; and
- positive raw uplift in seven of eleven groups, or `63.6364%`.

It captures `47.2832%` of the compact no-op/near-full/full oracle opportunity
over fixed full search. All eight original selection gates pass, including
strict raw and corrected-normalized quality, work, charged rate, group
fraction, opportunity capture, and maximum harm.

Every leave-one-group-out fit shown in the result uses the same one-split tree
and threshold. That is encouraging but not independent evidence: the feature
family and threshold candidates were exposed to these eleven groups.

## Interpretation

The earlier result was not a subtle tie. Using the wrong payoff span changed
which model family maximized the declared grouped objective and reversed the
screen verdict. Positive scale invariance was necessary but insufficient; a
measurement can be perfectly equivariant while normalizing by the wrong game.

The candidate's behavior is also narrower than the phrase "adaptive width"
suggests. It predicts whether to run full search at all. It does not safely
remove individual bet or raise branches. Its split may partly distinguish
dense factorized belief changes from two-deal blocker changes and may depend on
the generated deal-count distribution. That makes fresh contexts, target-type
breakdowns, and subgroup stability essential.

Exact acceptance remains stronger on these revealed labels, and the
policy-delta tape remains exact. The causal rule is cheaper because it can skip
solving before seeing a candidate; exact recertification can only reject after
the candidate cost has already been paid. They are complementary scheduler
stages, not substitutes.

## Fresh replication contract

Freeze the exact one-split procedure, full action universe, solver regime,
feature boundary, conservative runtime charging, and all original gates. Use a
new seed and at least twenty new development board groups. Generate `b3r1` only
as an unchanged compact-oracle diagnostic; it may not enter the fixed rule.

If the fixed rule passes, advance it as the transparent causal baseline for
reduced multiplayer and future learned schedulers. If it fails any strategy,
group-transfer, harm, work, or rate gate, retain full search and do not adjust
the threshold on the new artifact.

## Dissent protocol

**Confidence:** very high that ADR-0044 used the wrong denominator; high that
the corrected held-in screen passes; low to moderate that the threshold
transfers to fresh boards and ranges.

**Opposing evidence:** four held-out groups still lose raw and normalized
quality, the positive-group gate passes by only one group, and one range-density
feature may encode artifacts of the synthetic target generator.

**Largest unknown:** whether changed-deal fraction predicts beneficial full
search on new group geometry rather than merely partitioning this artifact.

**Cheapest falsification:** apply the frozen threshold once on freshly generated
development groups and require all original joint gates without refitting.
