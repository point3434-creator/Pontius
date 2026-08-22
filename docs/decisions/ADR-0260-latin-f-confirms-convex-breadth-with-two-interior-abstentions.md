# ADR-0260: Latin-F confirms convex breadth with two interior abstentions

- Status: accepted fresh confirmation; prospective live-shadow preregistration authorized
- Date: 2026-08-22
- Implements: ADR-0259
- Clean preregistration commit: `9f623e65bb6cdb7da039fce1285ec5d9bb7c059d`
- Result: `experiments/results/h32-latin-f-convex-retreat-confirmation-v1.json`
- Result SHA-256: `3bc21cee836f7327d967ef363ff367b7538d1992da052903dab21a1d6450a73b`

## Formal result

Every provenance, Latin-E parent, untouched-target, source, bettor, acting-seat,
posterior, checkpoint, blueprint, warm-start, topology, affine-row, resident-
row, new-cut, master, projection, campaign-barrier, reconstruction, exact-
oracle, timing, memory, finite, immutable-emission, no-global-optimality, and
no-population gate passes. The clean campaign completed in `112.526 s`.

All six Latin-F candidates froze before the first final label. Every target is
disjoint from Latin-E and received its first final retreat evaluation. All six
certificate reconstructions passed before their oracles. No candidate was
emitted and no Latin-E quantity selected or tuned a Latin-F candidate.

The preregistered confirmation branch passes exactly at its breadth floor: four
of six targets are materially accepted, the accepted set contains two balanced
and two blocker-heavy ranges, and all six measured and effective conservative
schedules fit.

## Four accepted, two principled abstentions

All six half-retreats are independently cap-feasible with zero recorded maximum
cap violation and all six raw exact values exceed `0.001`. The two rejected
targets fail only the stronger `1.48e-9` interior-slack contract:

| Target | Family | Actor | Raw exact value | Minimum cap slack | Shadow outcome |
|---|---|---:|---:|---:|---|
| `panel_1/balanced/checks_then_bet_seat5` | balanced | 4 | `0.0046825333` | `3.0e-9` | accept |
| `panel_1/blocker_heavy/checks_then_bet_seat0` | blocker-heavy | 5 | `0.0192926362` | `3.0e-9` | accept |
| `panel_2/blocker_heavy/checks_then_bet_seat1` | blocker-heavy | 0 | `0.0152754344` | `1.49999988e-9` | accept |
| `panel_2/balanced/checks_then_bet_seat2` | balanced | 1 | `0.0062591718` | `3.0e-9` | accept |
| `panel_3/balanced/checks_then_bet_seat3` | balanced | 2 | `0.0079707052` | `1.37419051e-9` | blueprint abstention |
| `panel_3/blocker_heavy/checks_then_bet_seat4` | blocker-heavy | 3 | `0.0048529755` | `1.24553792e-9` | blueprint abstention |

The shortfalls are `1.06e-10` and `2.34e-10`. They are small relative to raw
guard but larger than the frozen allowance, so rejecting them is the contract
working rather than a numerical tie. Both retain positive value and exact cap
feasibility, but neither may be called accepted or delivered. Actual policy is
the immutable blueprint on those targets, as it is on every development-shadow
target.

Do not rescue these rows post hoc with a smaller retreat factor or another
oracle. A future factor/adaptive-retreat study requires new preregistered
contexts and a complete added-oracle ledger.

## Value and breadth

The four accepted targets deliver pooled exact value `0.0455097758`. Including
the two non-emitted interior failures, the raw positive pool would be
`0.0583334565`; that number is diagnostic only. Latin-E and Latin-F together
deliver accepted pooled value `0.1104382938` across ten accepted targets.

Across the two fixed panels, every one of the 12 exact half-retreats is positive
and cap-feasible, while ten clear the stronger interior and deadline contract.
This is substantial breadth evidence that optimizing the full one-seat axis
solves the direction-poverty problem exposed by the regret-ray campaigns on
this reduced-h32 continuation family. It is not a binomial population estimate:
the panels are structured Latin coverage over retained boards and source
families, not an IID sample from poker play.

## Construction, wall clock, and memory

Latin-F extracts eight genuinely new response facets with cut counts
`1, 0, 3, 1, 1, 2`. One additional resident response residual is classified on
the final target; its row matches the exact oracle within `1.67e-16`, and its
`1.75511172e-9` residual remains inside the verified `1e-8` master ceiling.
Every new signature is cut and no target exceeds one round.

Measured live ledgers range from `5,373.951` to `9,328.933 ms`. The effective
conservative ledger remains `13,967.6157 ms` on every target, preserving
`1,032.3843 ms` of hard-boundary headroom. Certificate-context reconstruction
ranges from `4,714.092` to `8,004.135 ms`, is identity-clean to `4.45e-16` on
source gains, and remains explicitly excluded from resident live work.

The maximum GPU-pool total is `8,080,590,336` bytes and minimum physical free
memory is `7,198,474,240` bytes, both safely inside the frozen gates.

## Confirmation and claims boundary

Accept the preregistered confirmation: at least four targets are materially
accepted, both families are represented, and all schedules fit. The result
authorizes only a separate prospective live-shadow integration preregistration
on new posterior identities with an immediate immutable blueprint fallback.

The combined Latin evidence makes no fresh fallback-dominance, IID population,
full-game, coalition, multiplayer-safe, multi-seat composition, cross-street,
global one-seat-optimality, exploitation, deployment, or broad poker-strength
claim. The two abstentions are part of the result and must remain visible in
every summary.

## Decision

Accept Latin-F as confirmation of the full one-seat convex generator for this
reduced-h32 continuation family. Retain the factor-`0.5` retreat, exact final
certificate, `1.48e-9` interior requirement, complete conservative ledger,
campaign-wide barrier, and immutable blueprint abstention unchanged.

Next preregister a prospective live-shadow integration on genuinely new boards
or posterior identities. The rule may attempt one bounded one-round convex
candidate and emit it in shadow only when the existing exact certificate and
deadline gates pass; otherwise it must take the blueprint. Do not use Latin-E/F
labels to choose targets or tune the factor.
