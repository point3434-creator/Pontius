# ADR-0226: Continuation rooting unbinds the complete 31-block library

- Status: accepted label-free engineering result
- Date: 2026-08-22
- Implements: ADR-0225
- Clean preregistration commit: `a9395c4`
- Result: `experiments/results/h32-continuation-root-ledger-v1.json`
- Result SHA-256: `4ffcf33e0c8f9cfbcae5dfbe0746c9a22f38a450513f036d75c0af4021c6d566`

## Formal result

Every provenance, parent, source, target, blueprint, warm-start, public-block,
convex-scope, five-opponent-charge, zero-own-contraction, affine-intercept,
memory, wall-time, finite, immutable-emission, and no-label gate passes. The
clean run completed in `154.951 s` from commit `a9395c4`.

The artifact contains exactly 12 device-fold warm steps, 372 continuation
candidate rows, 372 own-seat affine rows, and 1,860 opponent-BR-conditioned
affine rows. It serializes zero quality rows, affine feature values,
certificates, or strategy labels. Maximum affine-intercept error is zero. Every
target emits only its immutable restricted blueprint.

## The wall-clock bottleneck moved

Continuation warm steps range from `719.799 ms` to `1,602.093 ms`, with a
median of `1,066.412 ms`. Complete per-candidate Tier-B cost ranges from
`33.580 ms` to `1,353.608 ms`, with a median of `111.424 ms`. The maximum
candidate cost within a target ranges from `613.897 ms` to `1,353.608 ms`.

This is a material end-to-end reduction relative to the complete-tree ledger
in ADR-0222, whose warm steps ranged from `4.822 s` to `8.805 s`, median
candidate cost was `200.410 ms`, and per-target maxima ranged from `3.894 s`
to `7.142 s`. The comparison attributes the measured path difference to the
continuation-root system as a whole; it does not isolate node count as the sole
cause.

Across each complete 31-block library, the five opponent rows touch 800 of
4,960 possible terminal contractions (`16.13%`). Maximum terminal middle rank
ranges from 73 to 119. The measured cost spread therefore remains real even
after continuation rooting, but its tail is no longer large enough to bind the
whole library under the cumulative ledger.

## The complete continuation library fits

With the 15-second street boundary, one-second immutable-emission reserve, and
10 ms one-winner affine-envelope reserve, the minimum conservative worst-case
safe K is 9. Per-target worst-case K ranges from 9 to 21, passing the frozen
minimum-six promotion threshold everywhere.

The deterministic public-tree-order cumulative rule fits all 31 candidates on
all 12 targets. Complete measured ledgers for warm step, all candidates,
affine-envelope reserve, and emission reserve range from `5.586 s` to
`10.391 s`, leaving `4.609 s` to `9.414 s` of measured headroom. This passes
the minimum-eight promotion threshold by reaching the library ceiling on every
target.

The cumulative result remains a development measurement, not a live deadline
guarantee. Its importance is narrower and stronger: at this exact library
width, selection capacity no longer forces a Tier-A prefilter or partial
structural slice. The deployment-shaped rule can price every continuation
block, select one winner, and retain blueprint fallback.

GPU-pool allocation peaks at `8,174,427,136` bytes and physical-free memory
never falls below `7,185,891,328` bytes. The existing single-target resident
layout remains inside the frozen memory gates.

## Decision

Accept the label-free ledger and authorize one separate fresh continuation-
root strategy preregistration on the same 12 targets. Freeze the live-like path
as:

1. one continuation-root warm step;
2. all 31 regret-vertex blocks in public-tree order, subject to a hard
   pre-emission clock guard;
3. complete six-seat affine rows for every completed block;
4. one winner selected by the full affine envelope's positive certified value,
   with deterministic structural tie-breaking;
5. one independent exact certificate on that winner only; and
6. immutable restricted-blueprint fallback for no positive envelope, failed or
   late proof, numerical failure, or deadline exhaustion.

The next preregistration must preserve the 15-second boundary and one-second
emission reserve, distinguish the affine proof from its independent exact
teacher, report abstention and delivered exact value per target, and make no
claim about candidate families beyond the frozen one-step regret vertices.
Do not reopen a proxy selector: at 31 blocks, the measured continuation path
does not need one.

No strategy has been populated. This result makes no strategy-quality,
opportunity-magnitude, selector-transfer, continual-resolving, deployment,
composition, or population claim.
