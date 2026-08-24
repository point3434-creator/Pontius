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

ADR-0344 now source-seals the first legal responder-raise keystone without
opening its result. A new checked-to heads-up river bridge derives all actions
and chip settlement from the exact six-seat betting kernel. Its frozen
six-strategic-node tree includes both a full raise and a legal short all-in that
the intentionally simplified legacy sizing game cannot represent. The opener
acts twice, so the behavioral shortcut must reject and sequence-form row
generation must match a separate 16-by-18 complete normal-form teacher. This
is a one-hand semantic source boundary only: no h4 coefficient, row-capacity,
multiway, latency, production-action, or strength result exists. The next act
in this lane is its sole exclusive-create invocation from the committed source.
The separate [prediction ledger](docs/PREDICTION_LEDGER.md) is reporting-only.

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
