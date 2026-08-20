# ADR-0121: Preregister sustained resident CFR trajectory

## Status

Frozen after ADR-0120 and before any h32 resident iteration-three-through-eight
timing or state label.

## Context

ADR-0120 authorizes device-resident leaf-adjoint CFR for the measured h32
one/two-step warm-search customer.  The next action-width games will need new
blueprints and therefore longer trajectories.  A two-step identity result does
not establish that Float64 differences remain controlled through repeated
regret matching, DCFR discounting, and sharp current-policy changes.

ADR-0113 already contains exact transferred checkpoint teachers at warm-search
iterations 1, 2, 4, and 8 for all four fresh-board target beliefs, plus the
literal transferred bill for every step.  Reusing those frozen teachers tests
the enabling mechanism without adding strategy labels or paying to regenerate
the incumbent.

## Decision

Run one resident trajectory through iteration eight for each combination of:

- balanced and blocker-heavy ranges;
- local blocker and dense all-seat strength shifts;
- the exact average-64 blueprint and original `0.1 * payoff span` warm mass.

At iterations 1, 2, 4, and 8, compare literal regrets, strategy sums, current
policies, and average policies with ADR-0113.  Cross-run state digests remain a
reported diagnostic; numerical semantic identity is gated at `1e-10` for
accumulators, `1e-9` for maximum policy probability error, and `1e-10` for mean
information-set TV.

The balanced/local trajectory is additionally serialized at iteration four,
restored into a pristine resident solver, and continued to iteration eight.
This is stored-object restart identity, not cross-run derivation: regrets and
strategy sums must be exactly equal, current and average policies must be
identical, and the final state digest must match exactly.

Use ADR-0113's stored transferred step bills as the incumbent.  Every target
must clear `1.5x` both marginally and with one complete six-seat cache charged.
The median resident bill for steps 3–8 may not exceed the steps 1–2 median by
more than `25%`.  The existing 12 GB GPU-pool and 60-second step ceilings remain.

## Interpretation

A pass is an enabling result, not a strategy result.  It permits resident CFR
to train the first wider public-tree blueprints and moves the next experiment to
the two-bet-size/no-raise tree.  A numerical drift failure retains residency for
the demonstrated two-step customer only.  A restart failure blocks resident
long-trajectory training until checkpoint semantics are repaired.  An economics
failure similarly keeps the narrower ADR-0120 disposition.

No gate is conditioned on strategy improvement, current-policy quality, or
whether the iteration-eight policy would be selected.  Those labels already
exist in the teacher and are outside this audit.

## Scope

The experiment remains one fresh river board, one bet size, equal stacks, h32
selected supports, two generated range families, and four existing target
beliefs.  Eight iterations do not prove 64-step source-training stability and
do not authorize earlier streets, side pots, wider actions, or full-range online
claims.
