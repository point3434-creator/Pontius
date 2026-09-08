# ADR-0329: Source-seal the direct closed finite-block greedy owner

- Status: accepted source-only complete adaptive greedy graph and failure-complete owner; every greedy price and candidate value remains unopened
- Date: 2026-08-23
- Follows: ADR-0328
- Baseline commit: `3b821e75ea2f8ee1a84aaec05d38585f4873e165`
- Greedy source canonical-LF SHA-256: `6e824b83c8789ae64f1859aa5536769a815aca5dd0480500268e335a3a6244f5`
- Greedy seal canonical-LF SHA-256: `d28ad43c7c80996f2a2ab4dd1990dd1f2cb04621afb901f7688bd0f38c4a59a9`
- Focused-test canonical-LF SHA-256: `26ac55fd54753febe4ac8632daf36fa1cc85acdc68691a5fc7c98b2812d72900`
- Greedy protocol SHA-256: `dc703d044b35d4820d4a1742b4295b35cb09af720f66a5e9a21e127edbb226b2`
- Greedy schedule SHA-256: `a6811bbd4131f73735e2336bb064443a7d30b07e73d36abbbab2e7ca6c91569a`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0329
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: With a clean worktree at the committed ADR-0329 source seal, invoke `run_and_retain_adr0323_closed_finite_block_greedy_development` exactly once into its reserved canonical artifact path; traverse only the sealed evidence-selected branch, stop without retry on the first consumer or numerical rejection, retain the first terminal artifact, and then commit its exact bytes plus a solver-free rebinder and the frozen development selection or rejection before constructing any transfer population, preparation artifact, production action, or alternative pricing proposer
- Front-Door-Blockers: no closed finite-block greedy price, recovery/excess curve, or selected development width exists; no fresh transfer panel, preparation ledger, six-player response model, live strategy bridge, h32/full-range result, earlier street, complete 15-second decision, or poker-strength result exists

## Decision

Accept and source-seal the additive
`pontius.fresh_action_width_greedy` owner before its first development price or
candidate value. It freezes the whole adaptive state graph, not only one
expected path: all 2,479 anchored subset arms at raise widths two through six
and all 7,848 legal one-raise parent-to-child transitions are immutable before
the first direct finite difference exists.

No development consumer was invoked while implementing, testing, or sealing
this source. Every focused control patches the public consumer to fail if
value-free graph construction reaches it. The retained ADR-0328 teacher is
named only by its exact campaign digest in the schedule; the source-only graph
builder does not read its width values or compute a greedy price.

This is still a reduced h4, two-live-seat, river fold/call research owner. It
cannot emit or apply a betting action, construct transfer, enter the Legal
Decision Spine, claim a 15-second fit, or select a production action width.

The inherited authority remains explicit. ADR-0318 binds HiGHS 1.12.0;
ADR-0319 requires one public HiGHS-DS call per canonical task; All 177 ordered
observations pass under ADR-0320, leaving the separate consumer eligible;
ADR-0321 retains caller-owned legal fallback; and ADR-0322 returns research
evidence or rejection with no action. ADR-0324's value-unopened remainder stays
value-unopened, ADR-0326's exact panel remains the only development population,
ADR-0327's exhaustive bounded development-teacher is unchanged, and ADR-0328's
solver-free teacher result is the only width authority.

## Complete adaptive graph

Each qualified context owns every exact min/max-anchored subset request. The
arm ledger is identical to the teacher's legal subset universe but uses a new
greedy task identity and result owner:

| Raise width | Exact arms |
|---:|---:|
| 2 | 16 |
| 3 | 120 |
| 4 | 408 |
| 5 | 828 |
| 6 | 1,107 |
| **Total** | **2,479** |

For every possible incumbent at widths two through five, the graph contains
one transition for each omitted kernel-legal raise, ordered by ascending exact
raise-to total:

| Target width | All possible parent→child transitions |
|---:|---:|
| 3 | 120 |
| 4 | 816 |
| 5 | 2,484 |
| 6 | 4,428 |
| **Total** | **7,848** |

This graph is a prospective branch catalog, not a call count. One invocation
visits exactly one incumbent per context and width. It calls 16 initial
width-two arms and respectively 120, 104, 88, and 72 candidates at target
widths three through six: exactly 400 prospective public calls. The 7,848
alternative edges are never all solved.

The schedule independently reconstructs the exact ordered anchored-subset
family for every context and width and rejects a plausible task census with a
wrong subset index, member, or order. Counts and unique digests are therefore
not allowed to stand in for the frozen combinatorial family.

The initial implementation accidentally recompiled each augmented LP once per
edge during graph validation. A value-free census exposed the needless work
before the seal. Validation now compiles and binds each unique task once and
uses immutable task ordinals for adjacency; graph construction fell from more
than two minutes to about 15.3 seconds without changing any task, transition,
or schedule identity. This is an offline structural diagnostic, not solve
latency or a 15-second capacity result.

## Semantic response closure

`OpponentResponseRowIdentity` names a context, exact raise-to total, distinct
reduced bet increment, responder private-type index, and semantic fold or call
action. It is never an LP row number, row count, bet index, constraint count,
dual coordinate, or action-set digest by coincidence.

Every task contains exactly both fold and call for each admitted raise and each
of four responder private types. A proposed `OwnRaiseBlockIdentity` therefore
contains exactly eight semantic rows. A transition is valid only when:

1. the augmented action set equals the incumbent plus the proposed raise;
2. the proposal's raise-to total and reduced increment map exactly;
3. incumbent rows and proposed block rows are disjoint;
4. their semantic union equals the augmented response-row set; and
5. the exact phase order is `own block -> opponent response closure ->
   certified solve`.

The task independently rebinds its consumer request, kernel legal-set digest,
compiled-LP digest, and response-row-set digest. Same-count corruptions that
replace a call with another fold reject. Thus closure is checked from semantic
membership, not inferred from a numerical coincidence or a quiet LP shape.
Standalone row-set identities also require equal nonzero raise/increment
widths, strictly increasing nominal totals and increments, and the exact h4
private width; one-raise blocks independently require h4.

This closure is complete only for the declared heads-up fold/call model.
Responder raises, later actions, and multiway responses remain absent and
block production use.

## Frozen price, choice, and gate arithmetic

For incumbent interval `[L_i,U_i]` and response-closed augmented interval
`[L_a,U_a]`, the direct finite-block price is prospectively frozen as
`[L_a-U_i,U_a-L_i]`, with the separately typed ADR-0323 nested-reversal
allowance used only to reject a material nested-set reversal. A price is not
formed before the augmented response block is complete.

At each target width, choose the candidate with the greatest certified
feasible behavioral lower endpoint. Exact lower-endpoint ties choose the
smallest raise-to total because candidates are sealed in ascending omitted-
raise order. No tolerance, upper endpoint, midpoint, price point, milliseconds,
or post-outcome exception can break that tie.

The selected subset retains both conservative comparisons:

- full regret: `[L_full-U_greedy,U_full-L_greedy]`; and
- width-matched teacher excess:
  `[L_teacher-U_greedy,U_teacher-L_greedy]`.

Both normalize by the context-derived `pot + 2 * effective_stack`; stack alone
cannot substitute. Aggregate recovery sums chip endpoints over all 16 contexts
before conservative division. It is not a mean of context ratios.

Five distinct nominal gate types freeze ADR-0323's exact conjuncts:

| Gate | Frozen requirement |
|---|---:|
| Maximum normalized full regret | `<= 0.005` |
| Mean normalized full regret | `<= 0.001` |
| Conservative aggregate-recovery lower | `>= 0.90` |
| Maximum normalized teacher excess | `<= 0.001` |
| Mean normalized teacher excess | `<= 0.0002` |

The development width is the smallest of three through six passing all five.
No passing width is a valid complete negative result. Terminal objects
recompute every gate from the retained 16 context paths rather than trusting
stored booleans.

## Failure and artifact boundary

The future runner owns the initial arm, every ordered candidate call, every
closed price, each exact choice, all four width summaries, and the final
selection or rejection. A typed consumer rejection stops immediately with its
exact task, transition, partial context, completed-round prefix, call count,
and exception chain. A price, round, or campaign arithmetic failure is a
separate numerical rejection. There is no retry, alternate backend, changed
branch, skipped candidate, or post-failure threshold change.

The canonical result schema retains every exact task and transition identity,
semantic response-row-set and own-block digest, accepted endpoint/gap record,
finite price, choice, teacher binding, regret, recovery, gate, failure, and
nested digest. The no-clobber wrapper reserves and fsyncs a `.partial` witness
before the first preflight or consumer call and publishes canonical
single-final-LF bytes only after a semantic terminal result. A successor must
commit the first terminal bytes and a solver-free rebinder; a rerun cannot
repair missing output.

Completed and execution-rejected terminal objects accept only the exact sealed
pool, qualification, panel, teacher, schedule, and greedy-source identities.
A merely well-formed 64-hex provenance field cannot impersonate this campaign.

## Source and protocol seal

The greedy source canonical-LF SHA-256 is
`6e824b83c8789ae64f1859aa5536769a815aca5dd0480500268e335a3a6244f5`.
Its adjacent manifest binds the maintained consumer, qualification, structure,
teacher, teacher-result, and seal sources. The seal source hash is
`d28ad43c7c80996f2a2ab4dd1990dd1f2cb04621afb901f7688bd0f38c4a59a9`,
the focused-test hash is
`26ac55fd54753febe4ac8632daf36fa1cc85acdc68691a5fc7c98b2812d72900`,
the protocol digest is
`dc703d044b35d4820d4a1742b4295b35cb09af720f66a5e9a21e127edbb226b2`,
and the complete adaptive schedule digest is
`a6811bbd4131f73735e2336bb064443a7d30b07e73d36abbbab2e7ca6c91569a`.

## Controls

Twelve focused tests pass in 31.320 seconds. The repository suite ran 1,342
tests in 396.863 seconds and finished `OK (skipped=2)`. The focused controls
cover canonical source,
dependency, protocol, and schedule seals; the complete arm/transition and
realized-call ledgers; consumer-unreachable graph construction; exact omitted-
raise ordering and anchored-family reconstruction; semantic fold/call closure,
same-count corruption, standalone ordering, and h4 enforcement; phase order;
lower-endpoint/smaller-raise selection; conservative endpoint and aggregate
arithmetic; nominal gate separation and gate-boolean rebinding; exact terminal
provenance; forbidden imports/action/transfer paths; typed zero-call preflight
failure; and canonical no-clobber retention with pre-run staging reservation.

Ruff remains unavailable in the repository virtual environment; no substitute
linter is represented as that gate.

## Consequences and next boundary

The direct mechanism is now invocation-eligible but value-unopened. With a
clean worktree at this committed source seal, call only
`run_and_retain_adr0323_closed_finite_block_greedy_development` once at the
reserved artifact path. A typed rejection is the result, not permission to
edit and retry.

A completed result may select or reject a development width under all five
frozen conjuncts. It still cannot construct transfer, claim population
confirmation, measure capacity, choose a production menu, or emit an action.
Although ADR-0323 permits a successor to derive the transfer seed from this
mechanism commit, this front door keeps transfer unopened until the first
development artifact and its solver-free rebinder are committed.

## Evidence classification and dissent

- **Known:** source and dependency bytes, all exact arm/transition identities,
  semantic response closure, the 400-call realized work rule, selection and
  gate arithmetic, terminal schema, and no-clobber boundary.
- **Reproduced without greedy solving:** 2,479 arms, 7,848 transitions, every
  request/legal/LP/response-row identity, and every possible omitted-raise
  order.
- **Observed on source-only controls:** same-count semantic corruption rejects,
  exact ties choose the smaller raise, gate booleans cannot drift, and graph
  construction cannot reach the consumer.
- **Unopened:** every direct finite-block price, greedy choice, recovery/excess
  curve, development selection, transfer context/value, and production path.
- **Hypothesis:** the sealed direct procedure recovers at least 90% of available
  aggregate gain and stays within the width-matched teacher-excess limits at
  the width-three teacher knee.
- **Rejected:** stale-row reduced cost as block value, row count as response
  identity, point or tolerance tie-breaking, and a source-only pass as quality
  evidence.

Supporting acceptance: the adaptive behavior is fully enumerated before
values, each candidate closes the entire declared response block, and every
future terminal state is independently serializable.

Opposing evidence: the development path deliberately repeats subset solves
already represented in the exhaustive teacher, and the reduced fold/call model
does not test responder raises or multiway response growth.

Largest unknown: whether lower-endpoint greedy selection follows the width-three
teacher knee with at least 90% conservative aggregate recovery and no more than
the frozen teacher excess.

Cheapest falsifier: the single now-authorized 400-call campaign; any typed stop
or failed conjunct rejects the bounded direct mechanism without relaxation.

Confidence: high in the source graph, semantic closure, temporal boundary, and
arithmetic; no confidence claim is made about values that remain unopened.

## Claims boundary

This decision establishes only a source-sealed direct closed finite-block
greedy owner for the qualified h4 heads-up fold/call development panel. It
reports no price, greedy choice, recovery, teacher excess, selected width,
transfer result, capacity fit, complete 15-second action, six-player response
closure, live strategy or betting action, h32/full-range result, earlier
street, blueprint, NashConv, AIVAT, league, coalition, or poker strength. No
revoked experiment, external publication, or thesis change is authorized.
