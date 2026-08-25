# Pontius

Pontius is a research project for building an adaptive successor to a
Pluribus-style six-player no-limit Texas hold'em agent. The objective is useful,
certified strategy improvement under a hard wall-clock boundary, not iteration
count.

The current research spine is an exact six-player river control at 32 hands per
seat (`h32`). It combines factorized beliefs, shared public topology, resident
GPU solving, unilateral-deviation certificates, and an immutable-blueprint
fallback. The authoritative target is maximum marginal chip-valued decision
quality per millisecond of attributable online compute, subject to one hard
15-second continuous response wall whenever the controlled seat acts and a
one-second emission reserve. Prior-street and opponent-turn computation may be
credited only through an exact matching prepared artifact; it never extends
the live response deadline. Earlier cumulative-street results remain historical
systems controls, not deployment or broad strategy-quality claims.

ADR-0308 installs that contract as `ActionClockLedger`, `PreparationBank`, and
`LegalDecisionSpineV2`. Exact event boundaries now start each action wall before
state-transition work, preparation claims are one-use and bound to the exact
public state plus semantic/source provenance, and late candidates fail closed
to a legal fallback. This is verified resource accounting, not evidence that
speculation improves play or that a complete decision fits the live host.

ADR-0290 carries ADR-0288's explicit-deal reference loop, built on ADR-0286,
across five complete 1,225/1,081/1,035/990 opponent axes on every street. Exact
rational public-action likelihoods update only their actor, hard card
disjointness is retained, board reveals filter every axis, and the unchanged
four-street hand remains inside its historical cumulative-street ledgers. The
immutable policy is deliberately passive and untrained; normalized full-width
marginals, scalable value contraction, action abstraction, a credible full-game
blueprint, resolver candidates, and strength evidence remain unconnected.

ADR-0292 rejects the first fixed action-sizing lattice before it reaches that
loop. Its exact legal lattice and rational off-tree projector pass all 45,456
three-chip states and 60,732 transitions, but the frozen reduced river panel
has only one informative context and v1 recovers none of that context's
full-over-minimum/all-in gain. The code remains a parked oracle and baseline;
any successor requires a fresh development/confirmation preregistration.

ADR-0294 rejects the dyadic successor on confirmation-panel power before
replay integration. V2 conditionally recovers 94.51% of the available gain and
halves v1's aggregate normalized loss, but only five of 24 deterministic
contexts are informative versus the frozen minimum of eight. Both candidates
remain parked; the next work is candidate-blind sizing-power diagnostics, not
another post-outcome fraction adjustment.

ADR-0296 rejects the subsequent candidate-blind pool qualifier: its first seed
reaches 12 material contexts, but the second reaches only 11 within the frozen
96-context cap. No candidate was evaluated and the third batch remains value-
unopened. A follow-up over-open incident is recorded explicitly; the maintained
successor now owns batch identity and stop state rather than trusting a caller
loop. The next work must test a richer reduced sizing game before v3.

ADR-0297 now freezes that next test without opening a pool or value. It changes
only the private-type width from three-by-three to four-by-four, retains the
candidate-blind full-versus-minimum/all-in comparison, and adds exact LP-work
ceilings. ADR-0298 seals three structural pools and their digests in a separate
value-free module before the owned runner invocation.

ADR-0299 records a clean pass: the three batches reach 12 qualifiers after 23,
24, and 32 openings, with numerical, diversity, teacher, and pivot gates clean.
The result authorizes only preregistration of one v3 mechanism and fresh dual-
panel evaluation; none of these development panels may fit or confirm v3.

ADR-0300 freezes collision-repair v3 before source implementation. ADR-0301
now records its exhaustively validated exact-legal source and immutable digest:
v2's two-pot action remains whenever distinct, and three-halves pot substitutes
only on a mandatory-anchor collision. Two exact fresh stream seeds are sealed;
ADR-0302 now seals their value-free 48-context representative family and
separate 96-context qualification pool. ADR-0303's candidate-blind full/narrow
screen reaches 24 unambiguous qualifiers after 60 contexts and seals the final
panel before candidate values. ADR-0304 now rejects v3 before integration: its
normalized-loss gates pass on both families, but the qualified panel recovers
only 80.05% of the available raw-chip full-over-minimum/all-in gain versus the
frozen 90% floor. V1, v2, and v3 remain parked; a successor requires a new
prospective mechanism and wholly fresh panels. ADR-0305 now freezes that
successor before code: v4 retains v3's set and uses exact-rational maximin
pot-odds filling to spend otherwise unused slots under the same seven-raise
ceiling. Three exact fresh streams and two separately gated qualified
replications are committed prospectively. ADR-0306 now freezes the value-free
v4 source after exhaustive legality, v3-inclusion, exact-capacity, projection,
and bounded-work checks. ADR-0309 now seals the value-free 48/96/96 fresh
structures, their raw attempt counts, and zero overlap with the finite prior
inventory. ADR-0310 rejects v4's ordered qualification: A reaches 24
qualifiers after 73 contexts, but B's full-integer LP at context 21 fails the
native solver's primal verification. No final panel or candidate value is
accepted, and the source remains disconnected from replay, blueprint, the
convex master, and resolving. The next gate is a prospectively preregistered
candidate-independent native-simplex robustness audit, not a v4 retry.
ADR-0311 now freezes that audit's exact micro and fresh sizing corpora,
metamorphic representations, backend options, independent bounds, and kill
criteria before any corpus source or new LP value. ADR-0312 now seals the pure
  unit-tagged compiler, 48 micro inputs, 64 fresh contexts, 177 bases, and 885
  exact representations without invoking a backend or opening an optimum. The
  ADR-0313 runner is now source-sealed with typed failure-complete observations,
  exact micro enumeration, original-coordinate sizing reconstruction, outward
  certificate plumbing, frozen environment/options, and the exact 2,655-call
  schedule. ADR-0314 now retains the complete 2,655-observation result. Every
  HiGHS dual-simplex and IPM arm passes, while native records 36 failures. The
  literal gate rejects because it over-specified the known regression's entire
  failing-row set instead of its recorded unique maximum row 215. ADR-0315 now
  source-seals the artifact-only correction and synthetic controls before any
  authoritative retained-evidence read. ADR-0316's temporally separated
  exact-digest reanalysis passes every corrected conjunct and makes HiGHS dual
  simplex eligible only for a later prospective replacement-adapter
  evaluation. No adapter, runtime or quality result, v4 revival, or consumer
  migration is authorized.

ADR-0317 separates two solver classes that ADR-0316's direction had blurred.
The rejected native simplex remains in the compact reduced-sizing oracle, so
the active source boundary is a certified canonical HiGHS dual-simplex adapter
for that oracle. The one-seat behavioral master already uses HiGHS; its
retained solve calls consume only 0.063%-0.151% of complete measured ledgers,
so persistence and specialization are parked under a prospective 5%
perfect-solver materiality trigger. No solver source, result, consumer, or
candidate is changed by ADR-0317.

ADR-0318 now source-seals that canonical sizing adapter. HiGHS-DS is an
untrusted proposer: exact normalized policy evaluation supplies a feasible
behavioral lower bound, and an outward-rounded trusted-box certificate supplies
the upper bound. Eleven analytic, bounded-teacher, corruption, source, and
runtime controls pass. No sealed 177-base validation, legacy consumer change,
candidate value, or production replacement exists yet.

ADR-0319 now source-seals the failure-complete canonical validation runner
without opening a retained base result. Its immutable schedule counts exactly
one public HiGHS-DS proposal for each of 177 canonical bases: 48 exact micro
LPs use exact vertex/certificate authority, while 129 sizing LPs use ADR-0318
and a second ADR-0313 reconstruction. Nine unsealed controls pass; the next
boundary is the single sealed invocation, not a consumer or action-width claim.

ADR-0320 retains that one authorized invocation. All 177 observations pass
with exactly one public proposal each, including 48/48 micro and 129/129 sizing
gates; the largest sizing certificate interval is `8.50e-11` chips. This opens
only a separately preregistered certified-v2 reduced-sizing consumer. No
consumer, six-player action-width mechanism, complete-decision latency, or
poker-strength result exists yet.

ADR-0321 now preregisters that additive consumer before source or fresh values.
It is limited to an exact two-live-seat river opening with a fold/call-only
responder, keeps kernel raise-to totals distinct from reduced bet increments,
and can return certified research evidence or a typed no-action rejection. It
cannot emit a production betting action or stand in for multiway response rows.

ADR-0322 now source-seals the implementation. Eleven unsealed controls prove
exact legal/context binding, nominal amount conversion, one-call solver trust,
source/runtime fail-closed behavior, complete exception chains, and no action
emission. No fresh ladder value, complete-decision timing, or strength result
is part of that engineering pass.

ADR-0323 now preregisters a fresh certified finite-block action-width owner,
not action-abstraction v5. Complete kernel-legal integer universes and
exhaustive anchored best-subset teachers are the bounded authority; direct
finite-block prices become valid only after the exact fold/call response rows
for the proposed size are closed. Development may choose a width, while one
commit-derived fresh panel only confirms or rejects it. No structure or fresh
sizing value exists at this boundary.

ADR-0324 now source-seals the value-free development structures. The fresh
SHA-256 stream retains 96 unique h4 contexts after 440 attempts, with exact
kernel universes of 7, 9, or 11 raises and 12,556 prospectively enumerated
anchored subsets at raise widths two through six. No sizing solve occurred,
and the transfer pool still has no constructor. Candidate-blind qualification
must receive its own source seal before the first value.

ADR-0325 now seals that candidate-blind qualifier without opening the pool.
Its 192-task schedule pairs each complete universe with its anchored
raise-width-two subset, classifies only conservative certified chip intervals,
and owns target, exhaustion, ambiguity, consumer-rejection, and unexpected-
failure evidence.

ADR-0326 retains its one authorized invocation. The exact prefix stops at
context 50 with 16 qualifiers, 35 nonqualifiers, zero ambiguity, and 102
one-call accepted arms. The canonical artifact rebinds every endpoint and
semantic identity without solving again; result SHA-256 is
`d8bcf79a08eed1af6fece257b4917424e71123574c4a99b858c7a7e93cf2a7f5`
and the 16-context development-panel SHA-256 is
`7757bfb37bc28f4a23707f9b4dfae9401ffb0afa016e87890d18a18117c66792`.
No intermediate-width value is open. The next checkpoint is source-only: seal
the 2,495-task exhaustive bounded teacher before invoking it.

ADR-0327 now passes that source-only checkpoint. The sealed owner freezes all
2,495 full-then-subset requests, conservative normalized regret, set-valued
teacher intervals, strict dominance, sole-survivor uniqueness, and a
reporting-only equivalence set that may honestly be empty. Nondominated-set
cardinality is retained as the plateau measurement; no milliseconds-based
secondary rule can edit it. A no-clobber staging marker is persisted before
any future value call and canonical bytes are verified before publication. No
development intermediate-width value was opened. The next boundary is exactly
one retained teacher invocation, not greedy pricing or an action-width selection.

ADR-0328 retains that sole invocation. All 2,495 calls completed, and the
4,975,258-byte canonical artifact independently rebinds every task,
request/legal/LP identity, endpoint, regret, normalization, survivor set, and
nested digest without a solver call. Width three is the first exhaustive-
teacher width to pass the preregistered full-regret maximum and mean limits,
but it is not a selected action width: the direct closed finite-block greedy
recovery and teacher-excess gates remain unopened. The next checkpoint is
source-only again: seal that greedy owner before any price or candidate value.

ADR-0329 passes that source-only checkpoint without opening a greedy value.
The owner freezes all 2,479 exact subset arms and every 7,848 possible
one-raise transition, including incumbent/augmented request, legal-set, LP,
semantic response-row-set, and own-block identities. One realized path will
make exactly 400 calls. Each proposal has complete h4 fold/call closure before
pricing, exact ties choose the smaller raise, all five development conjuncts
recompute from retained evidence, and a no-clobber artifact witness exists
before any future call. The next boundary is its single retained invocation;
transfer and production remain closed.

ADR-0330 records that invocation as an artifact-boundary failure, not a sizing
result. The completed-result path certifies that all 400 calls occurred, but a
self-referential width-gate digest raised `RecursionError` before publication.
No final artifact, price, curve, or selected width survives; only the exact
58-byte `.partial` witness remains. The digest cycle is repaired, both public
campaign entries are permanently closed against replay, and the next eligible
work is a source-sealed non-replay study on a new untouched population with
synthetic success serialization and a write-ahead evidence journal before any
new value.

ADR-0331 preregisters that recovery without creating its population or opening
a value. Its seed derives only from committed ADR-0330 state; all 96 new
semantic contexts must be disjoint from all 96 original development contexts.
Before a solver-bearing successor is eligible, one value-free owner must pass
a canonical 402-record synthetic success journal, self-free hash chaining,
append/flush/`fsync` receipts, exact prefix recovery, and retained torn-tail
controls. Qualification, teacher, greedy, transfer, and action paths remain
closed.

ADR-0332 passes that value-free source gate. The new compiler accepts 96 unique
h4 contexts after 551 attempts and proves semantic disjointness from every one
of the original 96 contexts. The durable journal is exclusive/no-clobber,
returns receipts only after flush plus `fsync`, and preserves exact verified
prefixes with untouched torn tails. Its 610,098-byte systems-only fixture
rebinds one header, 400 observations, four populated width summaries, five
distinct gates, and one terminal. The fixture's fake width three is not sizing
evidence. Replacement qualification remains value-unopened and must receive a
separate source seal next.

ADR-0333 now supplies that source seal without opening a replacement value.
Its exact 192-task schedule runs complete universe then anchored width two per
context and stops at qualifier 16 or the first distinct exhaustion, ambiguity,
nested-reversal, typed-rejection, or unexpected-exception boundary. Every next
call requires the preceding post-`fsync` receipt. Accepted evidence retains an
exact policy and dual hint so the solver-free reader reconstructs both certified
endpoints rather than trusting journal hashes. Synthetic target, failure, torn-
tail, fully rehashed corruption, and append-failure controls pass.

ADR-0334 retains that one public invocation without retry. Its exact
391,986-byte journal contains one header, 98 accepted one-call observations,
and one target terminal after 49 complete contexts: 16 qualifying, 33
nonqualifying, and zero ambiguous. A solver-free rebinder reconstructs every
policy lower bound, dual-certified upper bound, classification, terminal, and
the exact 16-context target-only panel while the campaign, consumer, and solver
paths are disabled. The journal records no elapsed time and is not a latency
result. The next boundary is source-only: seal the new panel's 2,113-task
exhaustive teacher before opening any width-three-through-six value. No selected
width or production action exists.

ADR-0335 now seals that replacement teacher without opening a value. Its exact
2,113-task schedule contains one full legal universe per retained context and
every anchored subset at raise widths two through six. Conservative interval
subtraction, set-valued nondominance, sole-survivor uniqueness, reporting-only
equivalence, exact payoff-span normalization, policy/dual witness rebinding,
post-`fsync` continuation, and distinct semantic/infrastructure stops are
fixed. A complete 6,616,076-byte synthetic journal proves the success-shaped
serializer and independent reader with all solver paths unopened. The next
boundary is the sole no-clobber teacher invocation from a clean commit, not a
selected width or production action.

ADR-0336 retains that sole invocation: all 2,113 real arms were accepted and
the exact 8,027,171-byte journal independently rebinds without a solver. Width
two passes the frozen maximum-regret conjunct but narrowly fails the mean;
width three is the first width passing both and is also the descriptive median
knee. Tail positions 9 and 11 retain certified-positive lower regret until
width four. Wider menus open large set-valued plateaus. This is an h4
target-panel teacher curve, not a selected mechanism, latency result, or
production action width. The next checkpoint is a source-sealed additive
376-call non-replay direct mechanism before any new value.

ADR-0337 now seals that direct owner without opening a price. The complete
graph has 2,097 anchored arms and 6,543 response-closed one-raise transitions;
the frozen adaptive path has exactly 376 prospective calls. Selection uses the
greatest behavioral lower endpoint and then the smaller raise-to total on an
exact tie. A 378-record solver-free synthetic journal proves post-`fsync`
continuation, dynamic branch rebinding, all five gate fields, and the complete
terminal path. Its fake width three is schema evidence only. The next
checkpoint is the sole no-clobber real invocation from this clean committed
source, not transfer, capacity, latency, action, or production width.

ADR-0338 retains that sole invocation as an exact 1,437,835-byte journal and
rebinds it without a solver or campaign call. All 376 arms were accepted and
all five frozen gates first pass at raise width three, including a 97.7775%
conservative aggregate-recovery lower endpoint. The selected third raise is
context-dependent across the 16 menus, so this is a development width rather
than a fixed ladder or production action width. The journal records no
latency. Next is a source-only, commit-seeded untouched transfer population
and semantic non-overlap proof before any transfer value.

ADR-0339 now seals that untouched transfer population without opening a value.
The pre-value source-commit seed yields the first 96 admissible contexts after
478 raw candidates, 13,587 prospective anchored subsets, and zero counterparts
in the exact 1,244-context enumerated prior inventory. A nonzero-base control
proves raise-to-to-increment conversion explicitly. Width three remains only
the selected development width. Next is a separately source-sealed,
candidate-blind transfer qualifier; no qualifier, transfer result, capacity
claim, or action exists yet.

ADR-0340 now source-seals the separate 192-task transfer qualifier and a
solver-free target-only panel rebinder. It preserves the full-then-width-two
order, unchanged classifier, first-16 stop, exact post-`fsync` receipts, typed
semantic/infrastructure failures, and independent real policy/dual witness
checks. A pre-seal repair makes a complete wrong-campaign first record reject
instead of appearing as an empty prefix. The 111,357-byte synthetic target is
systems evidence only; the prospective real artifact remains absent. Next is
the sole no-clobber transfer-qualification invocation from this committed
source, not a teacher, width-three result, latency claim, or action.

ADR-0341 retains that one permitted invocation as an exact 378,108-byte
journal. It reached the frozen first-16 target after 47 contexts and 94 accepted
one-call arms; 31 contexts were nonqualifying, with no ambiguity, rejection, or
retry. The solver-free result owner seals the exact target panel and rejects
byte, campaign, terminal, witness, or panel-identity drift. This qualifies a
fresh transfer panel; it does not confirm width three. Next is a source-only
transfer-confirmation owner that applies the frozen context-local width-three
mechanism without width reselection and retains the all-conjuncts gate.

ADR-0342 now source-seals that confirmation owner without opening a real
width-three value. It reuses the 32 exact retained full/width-two arms as prior
evidence and schedules only 126 new width-three candidate calls. Those calls
simultaneously run the frozen lower-endpoint/smaller-raise mechanism and form
the exhaustive width-three interval teacher. The owner normalizes only by each
context's explicit payoff span and requires all five unchanged conjuncts;
partial passage is a completed rejection, not confirmation. Distinct consumer,
numerical, unexpected, and infrastructure terminals preserve exact durable
prefixes. Complete confirmed and rejected synthetic journals pass, but are
systems fixtures only. The prospective real artifact remains absent; next is
the sole no-clobber confirmation invocation from the committed ADR-0342 source.

ADR-0343 now retains that sole invocation. All 126 real candidate calls are
accepted, the exact 16-context panel completes, and every unchanged conjunct
passes. The conservative gate reports maximum normalized full-regret upper
`0.00032224468507681322`, mean upper `0.000049192473917409513`, aggregate-
recovery lower `0.9723098159302147`, and maximum/mean teacher-excess uppers
below `1.56e-14`. A solver-free owner rebinds the exact 445,731-byte journal,
all witnesses, context-local menus, teachers, and gate identities. Width three
therefore transfers on this untouched reduced panel. It remains context-local
reduced-game evidence, not a universal ladder, full-width production strategy,
complete action-clock result, or strength claim.

ADR-0344 source-sealed the first legal responder-raise keystone before opening
its result. A new checked-to heads-up river bridge derives all actions
and chip settlement from the exact six-seat betting kernel. Its frozen
six-strategic-node tree includes both a full raise and a legal short all-in that
the intentionally simplified legacy sizing game cannot represent. The opener
acts twice, so the behavioral shortcut must reject and sequence-form row
generation must match a separate 16-by-18 complete normal-form teacher. This
is a one-hand semantic boundary only: no h4 coefficient, row-capacity,
multiway, latency, production-action, or strength result follows.

ADR-0345 retains the sole invocation from clean commit `ff2b8ce`. All 24
frozen gates pass in a 7,400-byte artifact: six strategic and eleven terminal
nodes match, the independent chip oracle has zero stored error, the legacy
short-all-in omission is detected, the behavioral shortcut rejects, and the
sequence-form result matches the 16-by-18 complete teacher at
`2.333333333333333` within the frozen tolerance. A solver-free owner seals the
artifact and source closure. The `0.791`-second tiny-game campaign is not an
action-latency result. Only a separately preregistered h4 coefficient
differential is authorized. The separate
[prediction ledger](docs/PREDICTION_LEDGER.md) is reporting-only; forecast 2
remains open with only its semantic conjunct observed.

ADR-0346 source-sealed the authorized h4 coefficient differential before
opening its result. The exact ADR-0345 public tree is widened to four hands per
player and 16 dyadically weighted legal deals. The repeated actor has 12
information sets and 32 sequence variables. Four payoff rows and two derived
gain rows will be compared coefficient-by-coefficient against a separate
Fraction enumerator, then rebound at six frozen acting policies. A coverage
response reaches both the full-raise and short-all-in final-response histories.
The teacher imports neither the Float64 subject nor the evaluator; no endpoint
responder selector is recomputed. This gate carries no row-capacity, selector-
stability, latency, action, or quality claim.

ADR-0347 retains the sole clean invocation in a 100,710-byte artifact. All 34
frozen gates pass. A solver-free owner rebinds all 192 serialized Float64/
Fraction coefficient pairs, all 36 affine/direct endpoint identities, exact
profile zero-sum, and both derived gain-row identities without importing the
closed runner, game, evaluator, teacher, or optimizer. Every retained error is
zero, and both repeated-actor final-response histories have nonzero coverage.
This crosses one finite h4 coefficient gate only. The 1.743-second tiny CPU
campaign is not response-row capacity or action latency. Next is a separate
responder-row-growth preregistration; selector stability, preparation-bank
recovery, multiway closure, off-tree actions, and full-width capacity remain
unopened.

ADR-0348 source-sealed the legal h4 responder-row-growth audit without opening
its target trajectory. A read-only observer wraps one unchanged production
generator call and retains complete response signatures, every 32-coordinate
row, restricted-master diagnostics, exact oracle work, independently rebound
conditioning, and canonical semantic row bytes. A separate Fraction pass uses
only subject-selected tapes. The 60-second subject and 120-second complete
walls are infrastructure guards, not action latency. A pass can authorize only
a separately preregistered selector-stability successor.

ADR-0349 retains the sole clean invocation in a 50,963-byte artifact. All 25
gates pass: the two inherited exact rows converge in one 18-pivot master and
zero rows are generated. The responder tape changes at the candidate but has
exact gain zero, so no cut is violated; that is not a selector-stability
result. A solver-free owner rebinds every tape, Fraction row and evaluation,
the `2^-53` final gap, conditioning, oracle counts, and 21,691 semantic row
bytes. The 0.686-second subject campaign is infrastructure, not action
latency, and the exact `27/64` finite objective is not poker quality. Next is a
prospectively frozen selector-window gate; full-width capacity remains a
separate lane.

ADR-0350 source-seals that selector gate before opening any h4 target value.
Four selector-free, downstream-relevant sequence-form rays—three public-block
one-step DCFR regret vertices and the retained-master proposal—are fixed by
full policy digest. A Fraction normal-fan teacher returns the honest three-
valued map `fixed` / `tie_unresolved` / `switched`, including exact unresolved
interval measure and separate tie points. Total-function tape identity alone
gates certificates; reachable-support identity reports behavioral and phantom
downstream changes without authority. Exact legacy breakpoints, fixed-tape
values, maximum-envelope direction, engineered crossing/tie controls, and 136
production selector calls on an untouched dyadic schedule are frozen. The
60-second selector and 120-second total walls are infrastructure only. A pass
can authorize a separate h4 selector-stable affine integration
preregistration, not full width, action timing, action quality, or strength.

ADR-0351 retains the sole 1,493,122-byte artifact but rejects that recorded
authorization. The exact fan map passes independent rebinding, including all
136 production values, exact breakpoints, active affine rows, and maximum-
envelope direction. Its own honest output exposed the bug: every acting-player
section has reachable `tie_unresolved` measure one, while the v1 certificate
reported scale one because a nonclosing slope bypassed the zero source margin.
A solver-free owner records four such violations and returns no successor
authority. `selector_window_v2` now fails closed at every source margin inside
the semantic reserve before inspecting slope. The old helper and public runner
are permanently closed.

ADR-0352 now source-seals the tie-aware active-row recovery without opening
its h4 result. Exact local maximizers are closed into complete total tapes and
all of their affine rows are retained. `selector_window_v2` is available only
to exact singleton sources; tied sources dispatch to the complete maximum
envelope after every v2 window fails closed. Both source and current pruned
tapes are serialized, while total-function identity remains the certificate
authority. The prospective same-fixture run is development integration only,
not untouched confirmation, full-width capacity, action latency, or quality.

ADR-0353 retains that run's first terminal as a bounded rejection. The exact
local-maximizer Cartesian product exceeded the frozen 256-tape per-sample bound
before any completed h4 section, affine row, or envelope was serialized. The
961-byte artifact and clean source closure now have a solver-free owner; the
public runner is permanently closed. The successor must preserve the total
active strategy set symbolically, keep reachable-support identity separate,
and validate a compact affine-row quotient against exhaustive controls before
another h4 target value is opened. This is representation evidence, not action
latency, full-width capacity, decision quality, or poker strength.

ADR-0354 source-seals the factorized successor with no h4 target value opened.
It uses two independent exact lexicographic passes to compute the minimum and maximum
directional slopes of the complete active response face without materializing
its Cartesian tape product. Total-function and reachable-support cardinalities
remain separate arbitrary-precision outputs, and the work ledger reports both
linear logical operations and integer bit lengths. The exact selector fan
still owns the full ray; the composed seam control catches a source-dominated
row crossing at one half. A shared tie-semantics registry now requires every
named consumer to pass its applicable controls. Next comes a separately
preregistered legal h4 directional-face diagnostic, never a replay of the
closed ADR-0352 runner.

ADR-0355 now seals that next one-shot diagnostic while all legal h4 face
outcomes remain unopened. It freezes four inherited directions, two target
players, eight composed fan/face sections, and 136 scheduled exact point calls.
The result must retain both cardinalities, both lexicographic extrema, every
active factor, complete fan geometry, and measurable work with zero tape
materialization. Cardinality, ties, crossings, slopes, and cell counts are
observations rather than gates. The clean committed invocation will write one
exclusive terminal; this is still finite h4 infrastructure, not full-width or
15-second decision evidence.

ADR-0356 retains and solver-free rebinds that sole 3,888,072-byte terminal.
All eight fan/face sections and 136 scheduled calls pass with zero tapes
materialized. The largest exact total face has 104,976 members but only one
reachable-support behavior, demonstrating why the Cartesian predecessor died
and why factorized face calculus is the right representation. The two live
responder crossings remain exactly `15/19` and `139/163`. This is a finite
same-fixture development diagnostic, not action latency or poker quality; it
opens only a separately preregistered tie-aware affine integration successor.

ADR-0357 source-seals that integration mechanism without opening another h4
value. `factorized_tie_aware_affine` treats the exact normal fan as the ray
authority and the two-pass factorized face as the point authority. Exact
source ties enter a maximum envelope with zero elected-tape scoring; exact
singletons alone may use selector-window v2. Synthetic controls match an
exhaustive small oracle, preserve repeated-actor 4-versus-3 identity, and
integrate a 4,096-member face with zero Cartesian tape materialization. A
separate exclusive h4 owner must still be preregistered, and any same-fixture
pass remains development-only pending untouched confirmation.

ADR-0358 preregisters that exclusive legal h4 owner while leaving its result
path absent. It freezes the four inherited directions by two target players,
reproduces every ADR-0356 section digest, dispatches exact source ties to the
factorized envelope and exact singletons to selector-window v2 or typed closure,
and retains complete point/ray/cardinality/work/epigraph summaries. The 180-
second subject wall is the sum of eight live builds only. Natural modes,
windows, pieces, cardinalities, crossings, and runtimes are outcomes rather
than gates. Invoke exactly once from a clean committed boundary; any pass is
same-fixture development integration, not confirmation, action latency, full-
width capacity, decision quality, or strength.

ADR-0359 retains that sole 259,550-byte terminal as a same-fixture development
pass. All 22 gates are true: four exact source ties use the factorized envelope,
four exact singletons use positive v2 windows, and zero tapes or actions are
materialized. The summaries contain 12 fan rows but ten interval-owning convex
pieces; two rows tie only at the endpoint. A standard-library owner rederives
the source faces, compact envelopes, seams, dispatch, work, aggregates and
gates while labeling omitted non-source factors, non-quotient rows, and the
live section digest authenticated-only. Untouched confirmation must use a
fresh sealed population and a complete reconstruction-ready schema.

ADR-0360 source-seals that fresh population without opening a target value.
Four first-in-stream legal h4 contexts are derived only from the clean
pre-result ADR-0358 source commit; none is filtered, skipped, or replaced by an
observed mode or value, and all are semantically distinct from the one exposed
development fixture. The successor contract freezes three one-step regret
vertices plus one converged row-growth proposal per context, 32 total affine
sections, complete raw fan/face/epigraph serialization, zero tape
materialization, bounded laboratory walls, and all-or-nothing interpretation.
The next step is a separate one-shot owner preregistration, not an invocation.

ADR-0364 retains and closes the sole ADR-0363 full-width-capacity invocation.
Its exact 798-byte artifact is a typed Windows telemetry failure: the untyped
`GetProcessMemoryInfo` boundary rejected before the reduced control or literal
target, so no capacity result exists. Explicitly typed PSAPI and Kernel32
diagnostics both succeed. The successor must be an additive source-sealed v2
owner with a new exclusive path; never patch or invoke v1 again.

ADR-0365 source-seals that v2 successor without opening a target. Explicit
Win64 signatures, dual native readers, same-PID PowerShell control, the pinned
GPU runtime seam, exact v1 lineage, and a new exclusive result path are bound.
The 512 MiB reader-delta allowance is telemetry-only. Invoke v2 once from its
clean source commit; it still answers only ADR-0363's narrow capacity question.

ADR-0366 retains v2's sole passing guard and representation rejection. Exact
persistent numeric lower bounds are 249.486 GB base, 437.434 GB bidirectional,
202.627 GB optimistic scalar, and 14.679 GB resident belief; every cap/reserve
check rejects before all target allocations and contractions. This retires the
current explicit-half-assignment storage, not exact full width itself. The next
gate is an exact non-enumerative card-conflict representation; truncation has
not been authorized.

ADR-0367 preregisters that representation's first algebra gate. Labeled
three-pair source deals may be summed into their six-card occupied masks only
when all three source seats are closed; every requested open seat must be on
the query/right half. The resulting disjointness operator is an exact
subset-containment inclusion-exclusion transform whose reverse is its
transpose. The frozen small-game controls include dense and current
FactorTT/open-mode differentials, source-seat permutation, fixed-card
projection, and cold-versus-topology-stable one-seat refresh. No source,
full-width capacity, latency, action, or truncation result is opened yet.

ADR-0368 closes that algebra gate. The exact bounded reference matches literal
compatibility, its labeled-record transpose, dense six-seat enumeration, and
the current FactorTT `left_to_right` open-mode path. Three-source-seat
permutation and one-seat refresh are canonically identical to their controls;
unsafe open-source or fixed-card requests fail closed. This proves the quotient
mechanism on finite games, not scalable construction. Complete full-width
memory, scratch, work, placement, and reserve bounds come next, before any GPU
or literal target source. A complete repository audit passed 1,732 of 1,733
tests with two expected skips; the one deterministic failure is the immutable
ADR-0365 pre-invocation test still requiring ADR-0366's now-retained result to
be absent. The sealed control is preserved and the lifecycle defect is explicit.

ADR-0369 now freezes the next checkpoint without opening hardware work. The
preallocation proposal uses implicit combination-ranked six-card source masks,
retains the 893,970 labeled four-card query records, and prices the exact
transpose of that same operator. It must account for the 176-column reference-
hand feature width, a safe 2,971-column envelope, streamed source/query scratch,
automata, forbidden tensor-train export, results, full source refresh, and
host/device reserves. A passing byte model will still leave GPU numerical
identity and the 14-second throughput question unanswered.

ADR-0370 completes that source arithmetic. The fixture layout peaks at
492,448,676 device bytes; the safe 2,971-column envelope peaks at
8,126,480,964, so both pass the unchanged fixed byte/reserve gates. The result
is deliberately not called runtime capacity: one source refresh still carries
81,711,241,920 containment additions, with no measured kernel or latency. The
next gate is a bounded-exact GPU numerical/throughput keystone, not a literal
full-width solve and not support truncation. Full discovery added no new
regression: 1,744 of 1,747 tests passed, two skipped, and the sole failure is
the already recorded immutable pre-invocation result-absence predicate.

ADR-0371 now freezes the bounded GPU mechanism before device source. Its exact
cardinality-layer recurrence lowers the fixture's logical containment bill to
9,789,072,480 scalar edge additions, but that arithmetic reduction is not a
speed measurement. The complete ten-card universe is the only executable
population. Direct-automaton forward/adjoint and affine-fold differentials,
full source refresh, deterministic repeatability, separate numerical
envelopes, exact work accounting, mutation controls, and reject-before-CuPy
allocation guards must all pass before any staged or literal-width experiment.

ADR-0372 closes that bounded gate: all 22 controls pass on the complete ten-
card population on the RTX 5080. Exact forward and record-level adjoint,
direct automaton, sunk/reach fold, current-stack normalized chip value, full
source refresh, query-only reuse, warm byte identity, fixed/live admission,
and five adversarial mutations agree. Cold/warm/source-refresh device sums are
0.4435/0.2958/0.4346 ms, explicitly reduced units with no 45-card or action
interpretation. A staged non-45-card scaling preregistration is next.

ADR-0373 now freezes that scaling experiment before implementation: complete
10/16/22/28/34/40-card axes, a rank-127/width-128 direct automaton, repeated
cold/warm/full-refresh/query-only/adjoint units, exact selected direct scans,
full dot products, allocation and work ledgers, durable first-terminal
evidence, and fail-closed stage/campaign walls. Its owner must be source-sealed
with the real journal absent and can never accept 45 cards.

ADR-0374 implements that owner and source-seals its complete work, allocation,
raw-evidence, CUDA-ownership, durable-journal, and solver-free reconstruction
path before any real stage. ADR-0375 retains its sole invocation as a zero-
stage missing-parent infrastructure failure and permanently closes v1 rather
than retrying it.

ADR-0376 source-seals the additive recovery. The repository now owns a tracked,
hash-bound artifact marker; v2 checks that marker, its fresh exclusive paths,
and both closed v1 paths before stage authority. Eight focused controls pass
without a real device call, and every ADR-0373 scientific field is unchanged.
The next capacity act is one clean v2 invocation, not a 45-card probe or an
action-quality result. Full discovery passed 1,782 of 1,785 tests with two
optional skips; its sole failure is the already recorded immutable ADR-0365
pre-invocation absence predicate encountering ADR-0366's retained result.

ADR-0377 retains the sole v2 journal as a complete non-target pass. All 126
gates pass at 10/16/22/28/34/40 cards, every pool returns to zero, and the
40-card requested peak is 10.046424 GB against 15.710814 GB live free memory.
The 40-card warm, full-refresh, query-only, and adjoint medians are 327.622,
296.192, 32.319, and 1,015.458 ms. Its 49,557.238 ms independent direct scan
is validation infrastructure and dominates the stage wall; none of these is a
solve or 15-second action measurement. Literal 45 cards remain uncalled. The
next capacity boundary derives production and validation lifetimes separately
and proves streamed validation before any target owner can be sealed.

ADR-0378 freezes that boundary without opening a target. The future source
model must sweep typed host/device array births and deaths, keep one complete
host reference plus a 64-MiB staging window, forbid full device references and
full dot-product temporaries, and release the forward state before allocating
the unique adjoint. It must prove bounded chunk coverage and literal byte
comparison without CuPy. Arithmetic passage will still not be live admission
or action latency.

ADR-0379 now passes the exact source model. The 45-card streamed schedule's
device peak is 11,755,029,796 bytes at the forward-dot phase and its host peak
is 9,353,336,216 bytes; forward state dies before the 9,645,290,380-byte
adjoint phase. The 12 GB numeric cap margin is only 244,970,204 bytes, and
allocator/runtime classes remain excluded. This is fixed arithmetic, not live
admission. A bounded 10/22-card CUDA seam must validate complete host-held byte
references, streamed dot numerics, lifecycle, and real allocation high-water
before a literal owner can be considered.

ADR-0380 freezes that bounded seam before implementation. Complete 10- and
22-card populations exercise both exact reduced closure and a two-chunk
76,403,712-byte source reference. One device unary is overwritten between
classes; complete host bytes remain authoritative; forward operands die before
the unique adjoint is allocated; and allocator pools plus physical free memory
are sampled after every ownership transition. The public seam takes no
arguments, and any other width—including 45—must fail before CuPy import.

ADR-0381 now passes the bounded CUDA seam. All 32 gates pass at both 10 and 22
cards; complete ten-card exact errors peak at `2.05e-15`, and the 22-card dot
error is `5.68e-14`. The mandatory 76,403,712-byte source reference crosses
two chunks, the observed pool-total high-water is 204,377,088 bytes against a
271,464,560-byte conservative bound, and the allocator returns to its exact
starting state. This validates validation plumbing—not literal 45-card
capacity. A separately preregistered one-shot target owner is next.

ADR-0382 now preregisters that owner without implementing or invoking it. The
future no-argument `.venv`/`-B` command gets one exclusive durable terminal,
fresh host/device admission, exact 125-chunk source streaming, named allocator
telemetry, and fail-closed release. Target pass, rejection, OOM, and
infrastructure failure are all permanent first outcomes. Literal 45-card
values remain unopened until a separate source seal is committed.

ADR-0383 commits that source seal without invoking it. The config hash-binds
the target, no-argument owner, standard-library rebinder, exact 35-allocation/
19-scientific-call ledgers, and source-only controls. The owner fsyncs its
header before config, Git, target import, or CuPy; the result is still absent.
The next boundary is one clean public invocation followed by a separate
artifact-only assessment, with no retry or smaller-width substitution.

ADR-0384 retains the sole literal-45 invocation. Its 21,663-byte journal
rebinds to `completed_pass` with all 27 gates true: exact full-width river
quotient forward/adjoint identity, live admission, modeled ownership, and
absolute pool release pass on the named RTX 5080. The 219.667-second campaign
and its 116.178-second direct validation oracle are laboratory evidence, not a
solve or action result. The next boundary is an actual legal river-context
quotient bridge, not truncation selection or a quality claim.

ADR-0385 preregisters that source-only bridge around one action-conditioned,
six-way legal river context with five complete 990-hand opponent axes. It
freezes the table-seat/local-card mapping and a reduced leaf-adjoint
differential before bridge source. The current showdown automaton is admitted
only for a 60-chip flat pot whose every possible tie split is integral;
odd-chip and side-pot contexts fail closed rather than being approximated.

ADR-0386 source-seals the bridge without executing a full-width quotient. The
actual-context host fixture is rank 175/width 176 with 893,970 complete query
labels; exact reduced settlement, quotient, transpose, open-mode, leaf-adjoint,
and paired-seat controls pass. Consumer-resident NumPy payload is 15,888,996
bytes, retained validation is 84,972 bytes, and the 79,216-byte warm view is
explicitly nonadditive. No action, action timing, or quality result is opened.

ADR-0387 prospectively freezes the next source-only consumer-capacity seam.
Global feature ranges `[0,128)` and `[128,176)` partition every state plus the
single reach feature 175 exactly once; partial numerator/reach values normalize
only after recombination. Forward records and adjoint occupancies now have
separate typed chunk contracts, full compatible/covector/unique-adjoint arrays
are forbidden, and forward storage must die before adjoint birth. The capacity
verdict, CuPy execution, full-width value, resolver, action, and 15-second gate
all remain unopened.

ADR-0388 source-seals that CuPy-free seam. Fifty-eight physical shape/dtype
rows produce a 15,973,968-byte host peak and a 9,910,940,332-byte device peak;
the fixed cap and minimum-physical reserve inequalities pass, with live
admission still absent. A complete exact ten-card rank-175 control proves the
128+48 forward, normalize-once fold, adjoint, reversed-order, chunk, and
transpose identities. This is source capacity and bounded algebra only: no
45-card value, device result, iteration, action, timing, quality, or truncation
decision exists.

ADR-0389 preregisters the additive actual-context CUDA consumer before source
or device values. It freezes globally offset-aware 128+48 kernels, distinct
forward/query/source chunk types, numerator/reach and transpose units, exact
work ledgers, 25 named allocation births, live-admission telemetry, complete
ten-card and multi-chunk 25-card device controls, and a durable one-shot owner
whose result remains absent. The next checkpoint is its bounded source seal,
not the actual 45-card invocation, a solve, an action, or a quality inference.

ADR-0390 retains that bounded source seal as a numerical rejection. The exact
ten-card campaign passes, and the 25-card campaign passes offsets, direct rows,
folds, adjoints, global chunk-independent byte identity, allocation, release,
and wall controls. Its unnormalized forward and transpose scalars are adjacent
Float64 values, leaving an absolute `0x1p-20` residual against ADR-0389's
separate `2e-10` ceiling even though the relative residual is `1.385e-16`.
The ceiling was not relaxed: no actual owner was source-sealed, the reserved
artifact is absent, and all 45-card counters remain zero. The next question is
a preregistered same-memory compensated-feature tiling, not a full-width call.

ADR-0391 now preregisters that arithmetic repair without opening its source.
Global logical ranges `[0,64)`, `[64,128)`, and `[128,176)` map to adjacent
high/low Float64 pairs in the existing 128-column workspace. Pairs stay
unevaluated through the operator and deterministic global reduction; exact
binary-rational contribution sums independently audit the reducer. The
original absolute and relative ceilings, complete 10/25 populations, chunks,
runtime, memory, and wall gates remain unchanged. No successor module, actual
owner, reader, artifact, or 45-card value exists yet.

## Current checkpoint

See the generated [STATUS.md](STATUS.md) for the current decision and immediate
work. [PROJECT.md](PROJECT.md) defines the contract, [ROADMAP.md](ROADMAP.md)
defines checkpoint gates, and [RUNBOOK.md](RUNBOOK.md) records the supported
verification environments.

## Quick start

The original exact CPU laboratory still uses only Python's standard library.
Set `PYTHONPATH` to `src`, then run its smoke test:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m pontius.experiment --game kuhn2 --solver lcfr --iterations 20000 --report-every 2000
```

The current wide GPU evidence path additionally requires the pinned SciPy,
CuPy, and CUDA runtime described in [RUNBOOK.md](RUNBOOK.md). The repository-
local Windows CUDA DLL bundle is discovered automatically when Pontius is
imported; the environment variable is now an explicit override, not a required
shell ritual. Use the pinned path for the complete regression suite and never
treat a reproduction of an already opened result as fresh evidence.
