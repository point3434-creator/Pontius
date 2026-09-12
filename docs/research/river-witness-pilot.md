# Fresh-board and replicated-hand-pool witness grouping pilot

The user approved setting up eight fresh boards, three separately seeded private
hand pools per board, and two range regimes: 48 cases, each with 96 holdings per
seat. This document fixes selection, computation and interpretation before any
pilot score is evaluated. Execution needs the controller's separate approval.

## Selection fixed before scoring

Selection seed/domain: river-witness-pilot-001. For attempt numbers 0 through 9,999,
sort cards 0..51 by (SHA-256 of UTF-8 seed|board|attempt|card, card). The first five,
sorted by card index, form a proposed board. No hand evaluation or solver result
is used in selection. Accept the first two boards in each of these disjoint bins:

1. Five distinct ranks, fewer than three cards of any one suit.
2. Five distinct ranks, at least three cards of one suit.
3. Exactly one pair of ranks, regardless of suits.
4. Any other rank multiplicities: two pairs, trips, full house or quads.

Within each bin retain acceptance order; concatenate bins in that order. Exclude
every suit-equivalent version of the four old development/holdout boards and all
previously accepted pilot boards. Equivalence is the lexicographically smallest
sorted board under all 24 permutations of suits. Fail if the attempt bound cannot
fill the panel. No reseeding or alternative panel is selected after scoring.

This is a reproducible, deliberately balanced texture panel, not a uniform sample
of naturally occurring river situations. Equal weighting of these bins is the
declared target for the pilot. Its results do not justify an all-board confidence
interval, a natural-play frequency average or a claimed statistical power level.

For each board, pool replicate in {0,1,2} and seat in {0,1}, rank all 1,081 legal
two-card holdings by SHA-256 of:

    seed|pool|comma-separated-sorted-board|replicate|seat|card0,card1

Use the holding tuple as the digest-tie breaker; take the first 96. The seeds are
fixed reproducible pseudo-random selections, not disjoint partitions. Pool overlap
is permitted. Both range regimes use the identical selected holdings; uniform
weights are one, while polarized weights are four for uniform-equity <=0.2 or
>=0.8 and one otherwise. These are the existing range definitions. Cross-player
card collisions are rejected only by the unchanged joint-range constructor;
every selected hand must have positive compatible support or the case fails.

Case order: board 0..7, then pool 0..2, then uniform/polarized. Plan.json contains
all 48 exact case descriptors. Its SHA-256 binds the board names and seeds as well
as executable source. Plan generation is selection/hashing only, with no fresh
board equity evaluation, feature construction, clustering or LP invocation.

## Unchanged candidate and controls

Keep the one-bet heads-up river game (pot 10, bet 5, stacks 20/20), exact-hand
payoff construction, control representations, four-column witness_advantage
features and anchored clustering unchanged. Do not alter any existing source.
The shared witness method is governed by river-witness-groups.md. Both player
group counts match the occupied uniform_equity_200 counts separately for every
board/pool/regime. Capacity may vary across cases; methods match within a case.
No CFR training, parameter search, iterative regrouping or winner fallback occurs.

There are no retained witness banks for these new cases. For each case generate
all four control groupings, solve their two asymmetric games, and use those eight
solutions to construct the fixed candidate. Solve its two asymmetric games too:
ten LP calls per case, 480 for the full pilot. Witness generation cost is now
included in the worker runtime. The candidate still receives full-hand oracle
information, so this is not an equal-information or practical-feature-cost claim.
All five grouping floors and all witnesses are retained. The uncompressed control
uses 96 groups per seat; compressed methods share the baseline's occupied counts.

Compile uniform equities once per board per process. Retain the selected ranges,
hand order, joint weights, deal count, provenance, control groups, control bank,
candidate features/groups, candidate witnesses and all signed comparisons in each
case file. The parent reconstructs the game and inputs from the plan, rechecks
every bank certificate and regenerates the candidate without using an optimizer.
Certificates retain the existing 1e-8-chip width bound and exact-rational arithmetic
on the stored binary64 payoff coefficients. They are not statistical intervals.

## Analysis: eight board units, not 48 independent boards

Primary comparison: candidate grouping floor minus range_equity floor; secondary:
range_response. Also report uniform_equity_200 and exact-hand. Negative favors
the candidate. Retain each signed numerical interval and classify lower/higher
only when the whole interval has that sign, otherwise overlapping.

Average the two regimes within each pool, the three pools within each board,
and then the eight board means equally. With all 48 cases present this equals
the case-weighted mean; verify that identity. Missing, duplicated or reordered
cases prevent a complete pilot claim. Never substitute a survivors-only headline.

Report all five mean floors, all case comparisons and sign counts, each board's
mean and its three pool means, results separately by range regime and texture,
and the worst case against each control. Report sample-standard-deviation formulas
(denominator n-1) descriptively across the three pool means within each board and
across the eight board means. Do not treat those as standard errors or construct
confidence intervals. Hand-pool replicates and range regimes on a board are
related observations; the deliberately selected texture strata also matter.
Predeclare leave-one-board-out means to expose dependence on a favorable board.
No alternate subset becomes the headline. No improvement threshold or stopping
rule is chosen after observing outcomes; all 48 cases are required for completion.

This pilot explores sensitivity to board and hand-pool selection under the two
fixed range definitions. It does not address all opponent ranges, larger hand
pools, more betting actions, six-max strength, BB/100 or cheaper feature generation.
Its descriptive variation can inform a separately designed confirmation study
with an explicit target population, meaningful effect/precision and sample-size
rule. This pilot itself supplies no all-board significance conclusion.

## Execution and preservation

Python 3.14.6, NumPy 2.5.2 and SciPy 1.18.0 in the existing separately pinned
research environment. Source/contract hashes, interpreter/output paths, cases,
selection seed and workload limits are pinned in the plan. New case bytes do
not exist beforehand: the frozen generation recipe and inputs bind them, and
the parent independently reconstructs their content before completion.

One sequential worker, one BLAS thread, 480 planned LP calls, each with a
five-second and 10,000-iteration limit. Worker wall timeout: 1,200 seconds.
These are stop bounds, not a runtime prediction or permission to exceed them.
Parent reconstruction, verification and I/O are outside the worker timeout.
No process RSS cap or peak-memory claim is imposed. Allocation tracing is refused.

Reserve a new output directory atomically. Retain the plan/start, captures,
worker receipt, each case and final summary/manifest. Worker success alone is
insufficient: successful parent exit and a valid final manifest are required.
Any failed/missing case, timeout, inconsistent result, certificate failure or
evidence-write error prevents success; failed outputs remain evidence, with no
automatic retry. Hard kills, power loss and hostile concurrent mutation remain
outside the existing recovery contract. Internal worker entry is not authority.

Build checks may select boards and hand pools without scoring. Executable
rehearsals use synthetic summaries or a two-hand case on the old first development
board, never the fresh 96-hand panel. One focused opposing review precedes the
bound-run approval request. All earlier computational sources, reviewed packets
and milestones remain unchanged; metadata additions preserve previous bytes.
No commit, push, adoption or new experiment is authorized by this specification.
