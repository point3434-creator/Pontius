# ADR-0153: Fresh-panel one-step action-width passes and all candidates breach caps

## Status

ADR-0152 executed once from clean commit
`5cc686ce0a38fbce974e51610d9f335e35b955c4`. All 21 corrected frozen gates
passed. Every one-step candidate breached at least one immutable blueprint cap,
all 24 arm selections retained the blueprint, and the top-level
strategy-quality claim remains null.

## Evidence identity

The 28,192,272-byte artifact is
`experiments/results/h32-fresh-panel-action-width-warm-step-v2.json`, SHA-256
`2d61f22b2a20e8aedde7ea38efedec9e4d61087470fe117984aebaf886596ea0`.
Its corrective config SHA-256 is
`dd59bc7bc2833e9fba2352acf6ab58280734e930534b743e5e5f17f5f94c119a`;
its wrapper SHA-256 is
`07e527c69708f99063adc1cd099a234460a33f44cc2fa47ddbae5e23c7cc6d68`.
The artifact records the unchanged ADR-0150 config and implementation hashes
and exact reproduction of ADR-0150's terminal `KeyError: 'wall_ms'` before
corrected aggregation.

Strict Git metadata records clean full commit
`5cc686ce0a38fbce974e51610d9f335e35b955c4`. Total wall time was
`2971.5229 s`, below the frozen `5400 s` ceiling. The exception-capture trace
is part of this corrected mechanism and inflates Python-visible timings; these
costs must not be compared naively with ADR-0150's rejected untraced attempt.

## Frozen mechanism result

All six source blueprints and 12 target belief and descriptor identities
reproduced. Both arms executed exactly one complete warm resident DCFR step on
every target, for 12 one-size and 12 two-size steps. Both arms finished before
the first target quality call. The verifier produced exactly 36 complete
two-size-game profiles: 12 immutable embedded blueprints, 12 embedded one-size
current-1 candidates, and 12 native two-size current-1 candidates.

Warm starts reproduced numerically within maximum probability error
`2.220e-16` and maximum mean total variation `3.437e-17`. Every compact policy
round-tripped, every policy and quality vector was finite, quality-vector sum
error was exactly zero, and maximum zero-sum residual was `1.139e-14`.

The largest complete step took `45.934 s`, the largest cache construction took
`33.380 s`, and the largest complete profile took `45.515 s`, all below their
frozen ceilings. Peak observed GPU-pool total was `8,289,012,736` bytes and
minimum observed physical-device free memory was `9,891,217,408` bytes.

## Strategy diagnostic

Every candidate was cap-infeasible:

| Arm | Cap-feasible | Scalar objective improved | Selected |
|---|---:|---:|---:|
| one size | 0 / 12 | 2 / 12 | 0 / 12 |
| two size | 0 / 12 | 0 / 12 | 0 / 12 |

The two one-size scalar improvements occurred on local-blocker targets:

- panel 1 / blocker-heavy: normalized reduction `6.5305e-06`; and
- panel 2 / balanced: normalized reduction `1.5205e-05`.

Both violated three seat caps and therefore remained rejected. The other ten
one-size candidates and all 12 two-size candidates both breached caps and
failed to improve normalized NashConv. Summed over the 12 targets, the
ungated candidate reductions were `-0.0051543` for one size and `-0.0068577`
for two sizes. These sums are descriptive only; they are not selections,
population estimands, or action-width rankings.

This complete-profile result sharpens the earlier cap-stop audits. It shows
that universal abstention is not merely an artifact of stopping verification
at the first violating seat. Most one-step candidates are both unsafe under
the immutable envelope and worse on the scalar objective. It also exposes two
cap-only rejections that are particularly suitable for the preregistered
clean-fringe rejection autopsy.

## The widened branch was exercised

Every embedded one-size candidate assigned exactly zero mass to bet `6`.
Every two-size candidate assigned positive mass to that branch at 20 to 29
opening information sets. Across targets, mean bet-6 probability averaged
`0.09368%`; target maxima ranged from `1.541%` to `4.420%`. The absence of a
two-size scalar improvement therefore cannot be explained by an identically
unused added action.

## Resource and work diagnostic

| Measurement | One size | Two size |
|---|---:|---:|
| Mean persistent cache bytes | `3.743 GB` | `3.556 GB` |
| Persistent-byte range | `2.711–5.101 GB` | `2.576–4.845 GB` |
| Mean cold cache construction | `3.420 s` | `23.869 s` |
| Mean complete step | `19.451 s` | `38.824 s` |
| Maximum complete step | `23.018 s` | `45.934 s` |
| Accumulator bytes | `196,608` | `390,144` |
| Mean total middle rank | `9,787.7` | `19,085.7` |
| Maximum middle rank range | `73–119` | `73–119` |

The scale-canonical/shared-topology two-size cache used about 5% fewer
persistent numeric bytes on average than the raw one-size cache, while taking
about seven times longer to construct. Its step was about twice as slow and
its accumulator and total middle-rank work were about twice as large. Peak
pool use remained safely below 12 GB. These are mechanism- and machine-bound
cost observations, not evidence that one action width is strategically
superior.

## Relationship to prior evidence

ADR-0149 found one certifiable non-blueprint one-size candidate after a
two-step candidate stream. This one-step audit does not contradict it: the
candidate horizon, candidate set, and common widened verifier differ. The
accepted ADR-0149 target was not used as a filter or gate here.

ADR-0137 and ADR-0141 also recorded universal fixed-cap abstention for one- and
two-size short-horizon streams on two revealed boards. The fresh panel now
extends that abstention pattern to three preregistered boards and complete
one-step candidate profiles, but still does not identify a general
action-width effect.

## Decision

Accept the corrected mechanism and preserve the exact artifact. Retain the
immutable blueprint envelope, common widened verifier, shared-topology cache,
and null top-level strategy-quality claim. Do not rank action widths, relax
caps, deepen only favorable targets, or promote either one-step candidate.

The next useful step is the separately preregistered clean-fringe rejection
autopsy discussed after the workload was frozen. It should classify every
probe in the cap-pass/objective-pass 2x2, decompose rejected candidates into a
frozen atomic direction library, measure directional slopes and admissible
radii on a shared geometric grid, recertify every packed union, and compare
generator value with a finite deterministic certified benchmark. It must keep
expiry explicit and composition false by default.

## Dissent

**Confidence:** extremely high in mechanism identity, complete-profile
exactness, cap infeasibility, and resource safety; high that one warm step is
strategically weak on this panel; very low that the result ranks action widths
at a useful training horizon.

**Opposing evidence:** two one-size candidates improved the scalar objective,
and ADR-0149 found one certifiable two-step transfer. Short-horizon safe value
is sparse rather than proven absent.

**Largest unknown:** whether cap failure is caused mainly by bundled acceptance
units, steep local gain sensitivity, poor generator direction, or true
objective exhaustion. The present complete vectors motivate that trichotomy
but do not identify it.

**Cheapest falsification:** replay the retained candidates through the frozen
clean-fringe atomic autopsy. Frequently certifiable atoms or recertified unions
would falsify an all-or-nothing reading of universal abstention; uniformly tiny
admissible radii would support genuine local narrowness.
