# ADR-0267: Preregister retained full-closure census

- Status: accepted retrospective preregistration before any full-convergence oracle
- Date: 2026-08-22
- Follows: ADR-0266
- Config: `experiments/configs/h32-retained-convex-closure-census-v1.json`
- Config SHA-256: `494b4d93a5e8e17b85e09446e01d291b672b7a3098203513010725d4bd8c0e3c`
- Runner SHA-256: `d2e80c94a6f929d059659fd3fec716b2f90da29e7de169ccc441aed7d1bd9598`
- Control SHA-256: `b2a2baf3d19421e48eb0313ed9b4dd3cd1af75a979d55751968a03f336e87efd`
- Inventory SHA-256: `f08465f7561924b7b9af0cc9de24624805a4f2949704c57e8dc276a0ab464c65`

## Question

Across every compatible h32 context whose strategy evidence is already open,
how many exact opponent-response multi-cut rounds are required to close the
one-seat convex master? Does the current one-round live budget close every
retained program, or does full one-seat optimization remain an off-clock
teacher on some contexts?

This is a retrospective optimization-label census, not a label-free replay and
not a fresh strategy experiment. Its purpose is to identify the distribution
that the single ADR-0247 keystone could not.

## Corrected inventory

The proposed count of 24 was stale. Four compatible opened panels now exist:

- all 12 Latin-A/B continuation identities from ADR-0228;
- all 12 Latin-C/D identities opened by ADR-0235;
- all 12 Latin-E/F identities opened by ADR-0258/0260; and
- all six post-call current-decision identities opened by ADR-0264.

Use all 42 in that order. They are unique by target ID and belief digest. The
36 Latin targets use the already-declared widest last-responder axis
`(bettor - 1) mod 6`, with 16 public nodes, 512 h32 information sets, and
1,024 behavioral variables. The six post-call targets use their sealed current
actor, one public node, 32 information sets, and 64 variables. Every source,
bettor, and acting seat occurs exactly seven times.

The six ADR-0266 post-fold identities are hash-excluded. They must receive zero
strategy labels in this run. No value, prior cut count, cap slack, timing,
range family, board, or position may select or reorder an eligible context.

## Frozen algorithm

For each target, reconstruct the pinned source, posterior, continuation,
restricted blueprint, resident response caches, and acting axis. Retain exactly
one resident DCFR warm step for byte-level methodological comparability with
the live spine. The master remains blueprint-conditioned and does not consume
that step's candidate; this run records that fact but does not remove the step
from the live contract.

Build six exact profile rows and the source best-response gain row for every
seat. Then repeat:

1. solve the sparse behavioral master over every accumulated row;
2. project its complete acting-seat policy;
3. run one exact all-six-seat oracle;
4. update the incumbent only if that exact candidate satisfies every cap under
   the `2e-11` cap allowance;
5. classify already-resident response signatures under ADR-0257's `2e-11`
   row-identity and `1e-8` master-residual ceilings; and
6. add every genuinely new epigraph-violating opponent response in one
   multi-cut round, with no row deletion.

Do not introduce seat ordering, partial-vector stopping, response-tape warm
starts, approximate rows, row aging, or a direction-library seed. Seat early
stopping is unsound without certified bounds on every unevaluated seat and is
outside this census.

## Bounds and stopping

The restricted master supplies a verified lower bound `L` on the minimum local
NashConv. The immutable blueprint and every exact-cap-feasible master candidate
supply valid upper bounds; retain the smallest as `U`. Report `U - L` after
every iteration.

Declare closure only when one exact oracle exposes no genuinely new facet, the
candidate is exact-cap-feasible under `2e-11`, and `U - L <= 1e-8`. Resident
LP residuals may be classified only under the frozen ADR-0257 controls. A
no-new-row state without cap and bound closure is a numerical stall, not a
success.

Stop a target after 32 completed multi-cut rounds or after 240 seconds measured
at a round boundary. Stop the entire invocation before starting another target
at 10,800 seconds. A clean cap hit is right-censored evidence; do not extend a
budget after seeing a hard context. Every master solve, oracle, and extracted
row also retains its 60-second engineering ceiling. Preserve the 12-GB GPU-pool
and 1-GB physical-free gates.

Replay the ADR-0247 Latin-D keystone inside the fixed roster. Require identical
first-round cut players and cut count and numerical agreement of its initial
bound, oracle objective, final bounds, and gap within `2e-11`. This is the
cross-version control for the new loop and for retaining the otherwise unused
warm step.

## Process gate and scientific branches

Process validity is independent of closure prevalence. It requires all 42
targets attempted in order; exact parent and identity provenance; correct axis
shapes; one warm step per target; exact initial/cut/profile identities; verified
master primal and dual residuals; monotone lower bounds; complete response
accounting; memory and resource gates; keystone replay; explicit retrospective
label counts; zero post-fold labels; and immutable-blueprint external emission.

If all 42 close by at most one cut round, record universal one-round closure on
this retained corpus and authorize a fresh confirmation. That still does not
estimate a deployment rate or retire direction machinery globally.

If all close but any needs two or more rounds, accept full convex generation as
an off-clock exact teacher while retaining the direction/ray path as the live
deadline fallback. If any target stalls or is censored, retain that fallback
and report the right-censored distribution. Do not collapse censored rows into
one-round failures or successes.

## Claims boundary

Full row generation can prove the global optimum of the frozen one-seat
behavioral program when its exact bound closes. The existing live engine is
bounded to one cut round and its independent certificate proves only the
emitted retreat's safety and value. Neither statement is a global multiplayer
equilibrium claim.

These 42 contexts are balanced but retained and non-IID. No candidate is
emitted. No direction-obsolescence, fresh transfer, deployment, composition,
cross-street, chip-EV, AIVAT, exploitation, full-width, or broad poker-strength
claim is authorized.

## Decision

Commit the runner, config, controls, this ADR, roadmap, and generated status
from a clean tree. Run the 42-target GPU census once. Do not pilot a target,
inspect a partial result, alter the order, raise a resource cap, or open a
post-fold strategy label after execution begins.
