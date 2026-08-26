# Architecture

## System boundaries

```text
game-core       legal state transitions, cards, payoffs, replay
exact-lab       tree enumeration, evaluation, best response, NashConv
solver-core     traversals, regret updates, sampling, policy extraction
belief          Bayesian ranges, blockers, legal joint-hand sampling
abstraction     card/action representations and dynamic insertion
runtime         CPU/GPU execution, batching, deadlines, telemetry
teacher         offline resolves and root-aware training examples
models          blueprint policy, leaves, actions, uncertainty
online-search   public-belief tree and residual policy improvement
cache           provenance, range distance, topology/value reuse
scheduler       current and speculative value-of-computation queues
evaluation      exact metrics, responders, leagues, variance control
```

## Exact legal decision spine

`no_limit_betting` is the reference public betting kernel for the charter game.
It uses immutable six-seat states and integer chips; posts the blinds; orders
preflop action left of the big blind and later action left of the button; and
tracks stacks, street/hand contributions, folds, per-seat last-action wager,
the largest full raise increment, and cyclic pending responders. One raise-to
action represents either an opening bet or a raise. Its legal-decision record
separates the player's own all-in ceiling from the amount another live stack
can contest.

The kernel implements the named Poker TDA full-bet profile. Short all-ins do
not update the full-raise increment. A previously acted seat regains a raise
only when the cumulative increase since that seat's last action reaches the
full increment; a seat that has not acted retains its option. Round closure
returns a unique unmatched top wager. Raw contribution layers are merged when
their live eligibility sets are equal, preventing a folded-only threshold from
creating a fictitious separately split side pot. Settlement splits each actual
pot independently and awards integer odd chips clockwise from the button.

`legal_decision_spine` is the preserved ADR-0286 historical controller for one
controlled seat. It applies opponent events,
opens the controlled legal decision, accepts a resolver candidate only while
timely and legal, and otherwise applies a caller-supplied immutable-blueprint
fallback. Its `StreetDeadlineLedger` accumulates explicit monotonic wall-time
intervals. The production hand factories construct and validate the initial
preflop state inside the first charged interval. Opponent or transport idle is
paused; event processing and any foreground or background agent computation
are charged. The same ledger spans all controlled actions on a street under
the superseded ADR-0282 contract.
Betting-state transition work is charged to the closing street; an exact
transition archives its immutable closing snapshot before resetting, and
fold/showdown freezes the final street record.

`holdem_cards` adds a separate explicit six-seat deal oracle and a future-blind
`OneSeatCardState`. The latter retains only the controlled private hand and the
currently revealed board. Its exact single-opponent compatible domains contain
1,225 combinations preflop, 1,081 on the flop, 1,035 on the turn, and 990 on the
river.

`full_width_belief` lifts those domains into five ordered opponent axes. Exact
rational unary weights and action provenance remain available while the
accepted `FactorizedCardBelief` supplies the rank-one Float64 backend and hard
pairwise card-disjointness factor. Public actions update only their actor's
unary; board reveals filter all five axes, including folded seats. Analytic
compatible counts and Cartesian counts remain distinct. The independent
`exact_collision_oracle` validates reduced supports, partitions, and marginals;
the architecture does not materialize or claim normalized full-width
five-opponent marginals.

`immutable_blueprint` is a digest-bound exact lookup keyed only by that visible
card state and the complete public betting history. A table hit may name any
exact legal fold, check, call, or integer raise-to. Missing entries use the
deliberately weak total rule check, else call, else fold; stale or illegal table
entries reject rather than silently becoming passive. This reference source is
not a trained or strategically credible full-game blueprint.

`full_width_reference_policy` is a second immutable reference source used only
to make action probabilities and the complete legal integer raise interval
explicit. It uses exact rational weights and a closed-form raise denominator,
has no deal/future/model/table input, and always makes check or call uniquely
modal. It is deliberately weak and is not a trained blueprint.

`legal_action_abstraction` and `reduced_river_sizing_oracle` are parked v1
controls, not members of the live decision spine. The former constructs a
bounded exact-legal integer lattice with explicit clipping/deduplication
provenance and an exact barycentric observation projector. The latter compares
candidate sizes with the complete bounded integer interval in a one-bet river
security LP and checks bounded projections against a separately enumerated
normal form. ADR-0292 records that the mechanics pass but the fixed sizes fail
the preregistered reduced-quality gate. Neither module may rewrite public
betting state, select an emitted action, or enter `reference_hand_replay` until
a new held-out successor gate passes.

`action_abstraction_confirmation` is the separately parked ADR-0293/0294
evidence generator. It binds a SHA-256 counter stream, unbiased Fisher-Yates
shuffle, structural showdown filter, exact joint weights, and 24 ordered
contexts to one canonical digest. Its dyadic candidate passes conditional
quality controls but the panel fails its minimum informative-context count.
The generator therefore supplies a reproducible negative control, not a live
source or permission to lower the power gate.

`collision_repair_action_abstraction` is the rejected and parked v3 candidate.
`capacity_filling_action_abstraction` is its value-free ADR-0305/0306
successor, not a member of the live decision spine. V4 rebuilds the immutable
v3 parent, preserves every parent action, and fills unused slots to at most
seven raises by exact-rational maximin spacing in responder pot-odds. Its
midpoint inversion checks only floor and ceiling integers, so work is bounded
by action width rather than chip depth. Refill rank, bracket, score, parent
digest, and source digest are immutable and reconstructively validated. The
source gate passes and ADR-0309 seals all three fresh structures. ADR-0310's A
qualification passes provisionally, but B stops on a native full-integer LP
primal-verification failure before any final panel or candidate value. V4 is
therefore rejected and parked; no v4 action may enter replay, blueprint,
convex-master, resolver, or strategy paths.

`fresh_capacity_filling_structures` is ADR-0309's candidate-free structural
boundary. It reconstructs the frozen representative, qualified-A, and
qualified-B streams with its own exact probability/context records and imports
only the exact river card evaluator. Canonical identities bind the ADR-0306
source, inherited SHA-256/Fisher-Yates semantics, filter, attempts, order, and
every context field. The three structures are sealed and finite-inventory
disjoint; no sizing value or candidate dependency is present. Qualification
occurs only in a separate owner after this structural commit.

`fresh_capacity_filling_qualification` is ADR-0310's candidate-blind
full-integer-versus-minimum/all-in owner. Its exact adapter binds every
structural and oracle field, it rejects the representative family before a
solve, and B construction requires the exact digest-bound A pass. A stops at
its twenty-fourth qualifier after 73 contexts and owns 24 independent bounded
teachers. B completes contexts 0-20, then emits a typed digest-bound numerical
failure on the full arm of context 21; it opens no later context or candidate
value. The owner is a parked negative-control/evaluation artifact, not a live
strategy dependency.

ADR-0311 prospectively freezes a candidate-independent LP robustness audit.
ADR-0312 implements and seals its value-free half. The pure
`reduced_river_sizing_lp` compiler preserves the legacy matrix bit for bit
while tagging dimensionless policy rows, chip-valued envelope rows, policy and
shifted-envelope variables, trusted boxes, and the objective shift separately.
The isolated structure/corpus modules own 48 exact bounded micro LP inputs, 64
fresh width-four contexts, the disclosed ADR-0310 regression snapshot, 177
ordered bases, and five exact row/variable/scaling/redundancy representations
  per base. All 885 materialized representations are hash-bound without a
  backend call. At the ADR-0312 boundary, No runner or sealed value existed.
  ADR-0313 adds the separately source-sealed
  `native_simplex_audit_runner`: exact Fraction vertex enumeration, frozen
  native/HiGHS adapters, transformed and original residuals, primal/dual map
  reconstruction, original-coordinate feasible sizing reconstruction, exact
  behavioral lower bounds, outward-
  rounded original-coordinate upper bounds, immutable failure-complete
  observations, and the variant-major 2,655-call schedule. The adjacent
  `native_simplex_audit_seal` prevents a changed runner or runtime identity from
  invoking the corpus. At the ADR-0313 boundary, only unsealed toy inputs had
  exercised these paths. ADR-0314 now retains the complete 2,655-arm canonical
  artifact: both HiGHS methods verify on all 885 representations, native has
  849 verified returns and 36 exceptions, and no runner failure truncates the
  schedule. The literal gate rejects because it equated the regression's
  unique maximum row with its complete above-allowance row set. This remains
  solver infrastructure; HiGHS is not a consumer and v4 stays parked. ADR-0315
  adds a separate `native_simplex_audit_reanalysis` trust boundary. It accepts
  only ADR-0314's exact canonical artifact, revalidates the complete schedule
  and every unchanged HiGHS conjunct, and models unique argmax identity
  separately from optional complete failing-set identity. Its normalized-LF
  source seal is checked before artifact read; it imports no solver, corpus,
  exact, reconstruction, certificate, or write path. At this source-only
  boundary only synthetic traces had exercised it. ADR-0316 now records its
  one temporally separated artifact read: all 2,655 observations and unchanged
  conjuncts revalidate, the 21-row failing set has unique maximum row 215, and
  the corrected gate has zero failures. This authorizes only a prospective
  replacement-adapter evaluation; no solver is connected to a consumer.

ADR-0317 splits that prospective work by LP class. The compact
`reduced_river_sizing_lp` is the class whose v1 consumer still invokes rejected
native simplex; its next boundary is a canonical HiGHS dual-simplex proposer
accepted only by original-unit policy/envelope reconstruction and an
outward-rounded bounded-variable certificate. The behavioral one-seat master
already rebuilds a SciPy HiGHS dual-simplex model. Its recorded
product-of-simplexes shape is favorable to persistence or decomposition, but
the retained perfect-solver ceilings are only 0.151% and 0.063% of complete
measured ledgers. That optimization is parked until a prospective certified-v2
ledger crosses the 5% materiality trigger. Historical behavioral-master v1
primal objectives remain uncertified as lower bounds under ADR-0284.

`certified_reduced_sizing_highs` is ADR-0318's source-sealed canonical adapter,
not a production consumer. It recompiles exact sizing inputs through the pure
unit-tagged compiler and calls only SciPy's public HiGHS-DS interface. Returned
primal and multiplier vectors are untrusted. Original dimensionless policy and
chip-envelope checks remain separate; policy rows are converted to exact
Fractions and normalized; an exact fold/call evaluator supplies the feasible
maximization lower bound; and the bounded-variable outward certificate supplies
the upper bound. Its import graph contains neither native simplex nor a
candidate owner. The adjacent seal binds the adapter, compiler, certificate,
runtime versions, and the future 177-base inventory. Only toy controls have run;
no legacy sizing consumer imports this adapter.

`certified_sizing_validation_runner` is ADR-0319's source-sealed, result-free
owner of the exact 177-canonical-base schedule. It counts one public HiGHS-DS
call per base and continues after every typed rejection. Exact micro LPs use
ADR-0313's generic HiGHS path plus rational vertex enumeration; reduced-sizing
LPs use ADR-0318 and then bridge only raw primal/multiplier evidence into
ADR-0313's separate behavioral/outward verifier. The runner admits no
transformed arm, native backend, legacy consumer, or candidate owner. Its
correctness gate requires 48 micro and 129 sizing passes; retained wall times
are diagnostics, not a speed qualification. No canonical invocation exists at
the source boundary.

ADR-0320 retains the runner's sole canonical campaign. All 177 tasks pass with
one public call each; 48 micro exact/certificate checks and 129 sizing
adapter/independent-reconstruction checks are complete, with no policy or
multiplier-sign clips. The maximum sizing interval is `8.50e-11` chips. This
opens only the architecture slot for an additive certified-v2 reduced-sizing
consumer. No module fills that slot yet, and neither the legacy oracle nor a
six-player resolver imports the adapter. Component timing remains diagnostic,
not a complete-decision ledger.

ADR-0321 prospectively narrows that slot before implementation. The additive
consumer is a research evaluator for one exact two-live-seat river opening and
a fixed fold/call-only response model, not a live decision maker. It must bind
the complete public state, exact range/payoff matrices, and a caller-supplied
kernel-legal raise-to subset; convert street-total raise-to amounts into
separately typed bet increments; verify source/runtime seals before exactly one
public proposal; and return certified evidence or a typed no-action rejection.
Actual responder raises and multiway rows remain outside this reduced model, so
the Legal Decision Spine continues to own every emitted action and fallback.

`certified_reduced_sizing_consumer_v2` now fills only that research slot under
ADR-0322's source seal. It rederives the exact decision from an immutable public
state, validates an explicit full or restricted kernel-legal raise-to tuple,
and converts nominal street totals to distinct nominal bet increments before
one counted public adapter call. Accepted records recompile and rebind their
request, action mapping, and LP identity; failure-complete rejections retain
their cause chain and require a caller-owned fallback. The module contains no
action constructor/application or legacy/native/candidate import. Its eleven
tests are unsealed controls, not a fresh sizing result or live strategy path.

ADR-0323 prospectively places a new value-free structure and research layer
above that consumer. The bounded authority is a complete kernel-derived
integer raise universe plus certified full/subset re-solves and exhaustive
anchored subsets at raise widths two through six. In the compact formulation,
one added size introduces opener policy coordinates and responder envelopes/
constraints together; it is therefore not an ordinary standalone LP column.
The first pricing mechanism uses a direct closed finite difference and records
the incumbent and augmented fold/call response-row identities. Any later
reduced-cost proposer remains untrusted until own blocks and opponent responses
alternate to closure. Check, private-range width, raise-action width, raise-to
totals, bet increments, chip regret, and normalized opportunity remain distinct
semantic objects. The future transfer population is derived only from a frozen
mechanism commit; no transfer structure or value exists yet.

`fresh_action_width_structures` now fills only the value-free portion under
ADR-0324. It has a local SHA-256 stream, core river sign evaluation, exact
two-live-seat betting states, complete kernel-derived integer raise totals,
and lexicographic min/max-anchored subset families. Its immutable pool has 96
contexts and its work ledger counts 12,556 future subsets without compiling or
solving an LP. The module exposes only transfer-seed derivation from a future
mechanism commit, not transfer construction. The qualification owner, regret
intervals, response-row identities, finite-block prices, and mechanism remain
separate absent layers.

`fresh_action_width_qualification` now fills the next source-only layer under
ADR-0325. It builds an immutable 192-task full/width-two schedule, verifies both
source seals before a public call, and owns conservative certified interval
subtraction, strict three-way classification, contiguous-prefix stop state, and
target-only panel extraction. Typed consumer failures retain the failed arm and
any completed full arm; unexpected failures explicitly distinguish known calls
from complete call accounting. The result digest binds float hex endpoints and
semantic request/public/legal/LP identities.

`fresh_action_width_qualification_result` is ADR-0326's solver-free retained-
artifact boundary. It pins the canonical 95,083-byte result, reconstructs all
51 opened contexts and 102 exact request/legal/LP identities from the betting
kernel, rechecks every float-hex endpoint and conservative regret direction,
and rebuilds the qualification and 16-context panel digests. It cannot call the
campaign runner, a solver, or an action path. The exhaustive teacher is now an
adjacent source-sealed layer under ADR-0327. `fresh_action_width_teacher`
reconstructs the exact 16-context panel and freezes 16 complete-universe plus
2,479 anchored-subset tasks before values. It owns conservative chip and
payoff-span-normalized regret, interval-max teacher envelopes, strict certified
dominance, all nondominated survivors, sole-survivor uniqueness, and a
reporting-only equivalence set that may be empty. Nondominated-set cardinality
is preserved as the plateau measurement; no secondary runtime rule can edit
the teacher set. Typed consumer/numerical stops retain exact partial evidence.
Its authorized wrapper reserves a no-clobber staging artifact before the first
consumer call and publishes canonical byte-verified JSON. The layer remains
unable to price a greedy block, select an action width, construct transfer, or
emit an action. ADR-0328 now retains its sole completed invocation in the
4,975,258-byte canonical artifact. The adjacent
`fresh_action_width_teacher_result` owner reconstructs every schedule task and
request/public/legal/LP identity, checks all float-hex endpoints, independently
recomputes regret, payoff-span normalization, envelope and survivor semantics,
and rebuilds every nested digest without importing a consumer or solver call.
It exposes immutable diagnostics only. The measured teacher curve makes width
three the first full-regret-only pass and finds 49 plateaus among 64 nontrivial
context-widths; neither fact is a greedy mechanism or production-width choice.

ADR-0329 adds the adjacent source-sealed
`fresh_action_width_greedy` owner. Its value-free adaptive graph contains every
anchored subset task and every legal parent-plus-one-raise edge, so the
eventual evidence-selected branch cannot invent a request after seeing a
price. `OpponentResponseRowIdentity` binds context, raise-to total, distinct
increment, responder type, and fold/call action; an eight-row own block must be
disjoint from the incumbent and its semantic union must equal the augmented
row set before the certified solve phase. The result owner freezes exact
lower-endpoint/smaller-raise choice, teacher-excess and aggregate-recovery
arithmetic, all five width gates, typed stops, and pre-call artifact
reservation. ADR-0330 records its sole invocation as an artifact-publication
failure: the completed-result path reached all 400 calls, but the width-gate
digest recursively called its own artifact payload. The repaired digest hashes
a self-free core and the artifact envelope adds that digest afterward. The
exact 58-byte partial witness is retained, the final result is absent, and both
public campaign entries now reject before I/O or solving. No transfer seed,
greedy width, or action can be constructed from the lost result.

ADR-0331 preregisters an additive replacement architecture without reviving
that campaign. A new value-free population owner must reproduce the ADR-0323
generator distribution from a commit-derived seed and reject semantic overlap
with every original context. Its journal uses a self-free canonical body and
outer record digest, a previous-envelope hash chain, and an append receipt only
after flush plus `fsync`. Readers expose an exact verified prefix and preserve
all invalid trailing bytes. A synthetic 402-record completed path must traverse
the real canonicalizer and rebinder before any solver-bearing source is
eligible.

ADR-0332 installs and seals that layer. `fresh_action_width_nonreplay`
constructs 96 ordered, unique contexts disjoint from the complete original
96-context pool and owns only value-free work identities. The adjacent
`durable_evidence_journal` accepts production construction only through
exclusive create, poisons after any failed append, and makes a post-`fsync`
receipt the only durable-success token. Generic recovery authenticates record
structure and preserves raw failure bytes; a campaign-specific rebinder remains
responsible for semantic task order and terminal reduction. The fully populated
synthetic path proves all 402 records, four nested summaries, and five distinct
gate fields serialize and rebind without recursion. Synthetic endpoints and its
fixture width are explicitly outside the research plane. Qualification,
teacher, direct mechanism, transfer, and action owners remain separate absent
layers.

ADR-0333 adds only the source-sealed non-replay qualification layer.
`fresh_action_width_nonreplay_qualification` binds the ADR-0332 pool to 192
ordered complete-universe/anchored-width-two requests and owns the sole future
ADR-0322 call site. Its write-ahead state machine admits the next arm only from
the preceding header or observation's post-`fsync` receipt. Accepted payloads
carry the exact policy and raw inequality-multiplier hint; the solver-free
rebinder independently reconstructs the behavioral lower bound and outward
certificate upper bound before deriving conservative regret. Typed consumer
rejection, nested-value reversal, ambiguity, unexpected owner failure, and
post-launch infrastructure failure remain different states. The latter
retains raw bytes, exact generic prefix/suffix, last-receipted semantic
evidence, and unknown unreceipted invocation status instead of masquerading as
preflight. The adjacent seal fixes the source graph, protocol, 192-task
schedule, prospective JSONL path, and synthetic target/failure identities.
At the ADR-0333 source-only boundary no real qualification journal or panel
existed, and this reduced h4 fold/call owner remained outside the Legal
Decision Spine.

ADR-0334 adds the read-only retained-result layer.
`fresh_action_width_nonreplay_qualification_result` binds the exact
391,986-byte/100-record journal, calls only the sealed semantic rebinder, and
requires the exact target campaign, terminal, 98 accepted one-call arms, 49
context outcomes, 16/33 classification split, and complete call accounting.
It exposes a panel only from that exact target terminal. The panel core binds
the population, qualification schedule, journal, terminal, ordered pool
indices, and ordered semantic context digests; its constructor rejects Boolean
indices, duplicates, range errors, and journal/panel cross-identity. Source
closure and tests tripwire the qualification runner, consumer, and solver, so
rebinding cannot open a value or action. The retained h4 panel is eligible only
for a separately source-sealed 2,113-task exhaustive teacher; it does not enter
the Legal Decision Spine.

ADR-0335 adds that source-sealed teacher as a separate research-only layer.
`fresh_action_width_nonreplay_teacher` rebuilds the exact ADR-0334 panel and
freezes 16 full requests plus every 2,097 anchored subset request before a
value. Accepted real payloads retain exact policy and raw dual witnesses; the
reader independently reconstructs both endpoints before deriving conservative
full-minus-subset regret, interval-max teacher envelopes, all nondominated
survivors, sole-survivor uniqueness, reporting-only equivalence, and
full-minus-teacher regret. Execution advances incrementally, but the terminal
reader reconstructs the entire durable journal independently. Only a post-
`fsync` receipt authorizes another arm, and nested reversal, consumer rejection,
unexpected owner failure, and phase-typed infrastructure failure remain
distinct. The 2,115-record completed fixture is explicitly synthetic. No
teacher value, width, action, transfer, or Legal Decision Spine input exists at
this boundary.

ADR-0336 adds a read-only result layer over that journal. The exact artifact is
retained as binary bytes; `fresh_action_width_nonreplay_teacher_result` checks
the byte and record identities before invoking the solver-free semantic reader.
Its width summaries carry separately typed inherited mean/maximum gate fields,
a descriptive median knee, and an all-context zero-lower boundary. The gate and
median coincide at width three; the all-context boundary is width four because
panel positions 9 and 11 remain a positive-lower tail at width three. Reporting
equivalence cardinality zero remains representable, while nondominated
cardinality zero is invalid. The layer has no writer, consumer, campaign,
transfer, preparation, or action dependency and cannot enter the Legal Decision
Spine.

ADR-0337 adds the separate source-sealed direct closed finite-block layer.
`fresh_action_width_nonreplay_greedy` freezes every anchored arm and every
parent-plus-one-raise transition on the exact ADR-0334 panel, but exposes only
one adaptive 376-slot call ledger. Each transition proves complete h4
fold/call response-row closure before the augmented certified solve. Selection
uses only the augmented feasible behavioral lower endpoint and then the
smaller nominal raise-to total on an exact tie. Width results recompute full
regret, width-matched teacher excess, chip-summed aggregate recovery, and all
five inherited gates from retained evidence. Execution is receipt-gated and
incremental; the reader independently derives the exact next task from the
prior selected incumbent, rejecting any valid arm from an unrealized branch.
This dynamic-branch rebinder is the journal authority; graph membership alone
cannot authorize a task.
The complete 378-record fixture is synthetic. No direct price, selected
development width, transfer, capacity, action, or Legal Decision Spine input
exists at this boundary.

ADR-0338 adds a read-only result layer over the retained direct journal.
`fresh_action_width_nonreplay_greedy_result` verifies the exact binary bytes
before delegating to ADR-0337's solver-free dynamic-branch reader. It pins all
376 accepted policy/dual witnesses, 16 context-result digests, four five-gate
digests, every selected menu and subset index, and the exact maximum
certificate-gap call. Raise width three is represented by the nominal
`RaiseActionWidth` type and remains a development-only result. The menus retain
integer raise-to totals rather than increments and vary by context. This layer
has no writer, consumer, campaign, preparation, latency, transfer, or action
dependency and cannot enter the Legal Decision Spine.

ADR-0339 adds the separate value-free
`fresh_action_width_transfer_structures` owner and adjacent source seal. The
owner derives its stream only from ADR-0337's pre-value source commit, retains
the first 96 structurally admissible contexts without collision skipping, and
binds their exact kernel raise universes and 13,587 anchored subsets. Its
cross-family inventory adapter explicitly converts a raise-to total to the
historical bet-increment meaning; a nonzero-base control prevents the two-chip
root coincidence from becoming authority. Exhaustive structural comparison
finds no counterpart among the exact 1,244 enumerated prior contexts. The
module imports no qualifier, solver, teacher, greedy result, capacity,
preparation, or action owner and supplies no value to the Legal Decision Spine.

ADR-0340 adds `fresh_action_width_transfer_qualification` as the independent
controller over that pool. It reuses ADR-0333's exact arm-evidence codec and
policy/dual validator, but owns a new 192-task schedule, protocol, campaign,
prospective `xb` journal, stop reduction, execution-failure boundary, and
target-only panel type. A panel can exist only for an exact first-16 target
terminal and carries context and artifact identities without endpoints,
regrets, policies, or values. Complete first records are checked for protocol
and campaign identity before generic torn-prefix recovery, so wrong synthetic/real provenance
cannot become an empty prefix. The source contains one dormant
consumer call site behind the uninvoked public wrapper; it imports no prior
result, teacher, greedy, capacity, preparation, or action path and cannot enter
the Legal Decision Spine.

ADR-0341 adds `fresh_action_width_transfer_qualification_result` as a read-only,
solver-free authority over the retained real journal. It pins the exact bytes,
record shape, campaign, target terminal, source commit, accepted one-call
evidences, contiguous 47-context prefix, 16/31 classifications, target panel,
and payoff-span-normalized threshold diagnostics. It reconstructs evidence
through ADR-0340 before accepting the byte hash and has no runner, consumer,
solver, action, or writer call. The panel publishes identities only; it cannot
confirm width three or enter the Legal Decision Spine.

ADR-0342 adds `fresh_action_width_transfer_confirmation` as the prospective
owner over that exact panel. Its schedule wraps each retained width-two request
as one response-row-bound incumbent, references each retained full-universe
interval without another call, and enumerates every anchor-plus-one-interior
width-three child. This yields 16 baseline tasks, 126 candidate tasks, 126
complete own-block/fold-call response transitions, and exactly 126 prospective
call slots; the 32 qualification arms remain separately identified prior
evidence. The candidate calls both execute the frozen behavioral-lower/smaller-
raise selection and populate the exhaustive width-three interval teacher.

The owner reconstructs real policy and dual witnesses before admitting values,
then derives finite-block prices, teacher envelopes, full regret, teacher
excess, payoff-span normalization, endpoint-summed aggregate recovery, and the
five unchanged gates. `completed_confirmed` requires all five; a completed
partial passage is `completed_rejected`, while consumer rejection, numerical
reduction, unexpected invocation state, and infrastructure failure remain
distinct. Its exclusive JSONL writer gates each call on the prior post-`fsync`
receipt and the rebinder rejects a complete foreign-campaign first record
before torn-prefix recovery. The public wrapper and its sole consumer call site
are dormant at this source-only checkpoint. No result enters the Legal Decision
Spine, and the synthetic confirmed/rejected terminals are not research values.

ADR-0343 closes that owner after its only public invocation and adds
`fresh_action_width_transfer_confirmation_result` as the solver-free retained
result boundary. It pins the 445,731-byte/128-record journal, source commit,
campaign, terminal, 126 accepted one-call witnesses, 16 context digests,
context-local selected menus, exhaustive teachers, and gate diagnostics. The
rebinder reaches `completed_confirmed`: all five unchanged conjuncts pass and
every context's unique teacher winner matches the frozen direct mechanism.
The result owner has no runner, consumer, solver, writer, action, or fallback
path. It confirms only reduced-panel transfer of the context-local width-three
mechanism and does not enter an action into the Legal Decision Spine.

ADR-0344 adds `legal_river_continuation` as an additive small-game adapter from
the exact six-seat `NoLimitBettingState` to the generic extensive-form game
interface. It accepts only a checked-to river with two live seats and
zero-contribution folded seats. Logical player zero is the exact root actor;
the other live table seat is logical player one. Strategic actions are the
literal semantic fold/check/call objects plus every integer raise-to in the
kernel's current bounds. Transitions and terminal net chip returns remain owned
by the betting kernel and its settlement path. The adapter enumerates literal
raise intervals and is therefore a semantic control, not a scalable runtime.

`responder_raise_semantics_keystone` was the one-shot ADR-0344 owner. It
freezes a six-chip checked-to continuation with six strategic and
eleven terminal nodes, including one full raise and one short all-in raise.
The public schema, root betting state, sources, finite teacher, and result path
were sealed before invocation. The repeated opener uses the existing sequence-
form one-seat master; the independent control enumerates 16 acting and 18
responder pure plans from direct utilities. An exclusive writer prevents
clobber or retry. ADR-0345 permanently closes this runner after its sole clean
invocation; no output can enter the Legal Decision Spine. Reopening strategy,
h4 extraction, selector stability, response-row capacity, multiway closure,
and off-tree observations remain separate successors.

`responder_raise_semantics_keystone_result` is ADR-0345's solver-free retained
owner. It reads only the exact 7,400-byte artifact, rehashes the ADR-0344 config
and all seven source-sealed inputs, and rebinds the six-node public schema,
eleven terminals, one full raise, one short all-in, zero-error chip oracle,
repeated-actor witness, complete teacher, generated bounds, response rows,
Jensen diagnostic, and all-pass gate vector. It has no prospective runner,
solver, game-action, write, or fallback path. The complete teacher remains the
independent numerical control from the sole invocation; this owner authenticates
and interprets rather than re-solves. The result opens only an h4 coefficient
preregistration and conveys no scaling, latency, action, or quality evidence.

`exact_sequence_form_coefficient_oracle` is ADR-0346's small-game independent
teacher. It reconstructs perfect-recall sequence parents, exact policy and
chance reach, direct utilities, realization coordinates, and terminal-to-last-
sequence coefficients with `Fraction`. It imports neither
`one_seat_convex_generation` nor `evaluation`; it is intentionally unsuitable
for runtime solving.

`legal_responder_raise_h4_coefficient_differential` was the prospective
failure-retaining owner for the same kernel-derived public tree at four hands
per player. Sixteen dyadic deals expand to 176 terminal paths and 32 acting
sequence variables. One Float64 subject call site and one Fraction teacher
call site produce four payoff rows; two gain rows are derived without an LP.
Every coefficient and constant is retained, then checked at six source-sealed
acting policies. A fixed coverage response reaches both repeated-actor final
histories. The source responder best response is computed once and never
reselected at an endpoint. ADR-0347 permanently closes this owner after its
sole clean invocation.

`legal_responder_raise_h4_coefficient_result` is ADR-0347's solver-free result
owner. It reads only the exact 100,710-byte artifact, rehashes the ADR-0346
config and its complete source closure, and validates all six 32-coordinate
rows. Hexadecimal Float64 values are converted to exact rationals and compared
with independently serialized reduced Fractions. The owner rederives profile
zero-sum, both gain-row algebra identities, and every payoff/gain endpoint from
the retained exact utility contexts. It imports no runner, game, evaluator,
coefficient primitive, teacher, or optimizer and has no action or write path.
It authenticates finite h4 coefficients only and cannot enter the Legal
Decision Spine.

`one_seat_row_growth_audit` is ADR-0348's laboratory-only read observer for
the source-sealed production generator. It temporarily instruments the
generator's existing module boundaries under a process-local lock, always
calls the original evaluation/master/row/oracle functions, and returns the
production result plus an immutable transcript. It adds no solver, row rule,
action path, fallback, or persistent state.

`legal_responder_raise_h4_row_growth` is ADR-0348's prospective one-shot owner
on ADR-0347's unchanged h4 fixture. It makes one observed production call,
retains every exact response signature and all 32 coefficients of every row,
and uses the independent Fraction enumerator to check the subject-selected
tapes without reselecting them. It separately records production-call and
complete-infrastructure walls, exact convergence/incumbent checks, restricted-
master diagnostics, oracle accounting, conditioning, and semantic row bytes.
It is not connected to the Legal Decision Spine and emits no action, selector-
stability label, full-width result, or strategy-quality row.

ADR-0349 permanently closes that prospective owner after its sole clean
invocation. `legal_responder_raise_h4_row_growth_result` is the solver-free
retained owner for the exact 50,963-byte artifact. It uses only the standard
library to rehash the ADR-0348 closure and rebind complete response tapes, both
32-coordinate Fraction rows, two exact evaluations, the one-master
convergence ledger, conditioning, call-graph oracle counts, semantic row bytes,
and infrastructure timing. It rejects fully rehashed coefficient and selector-
tape mutations against the result protocol. It imports no runner, observer,
game, evaluator, optimizer, action, or write path and cannot enter the Legal
Decision Spine.

`legal_h4_selector_directions` is ADR-0350's selector-free policy-family
compiler. It produces three one-step DCFR regret vertices partitioned by
public-history block and reconstructs the retained ADR-0349 restricted-master
proposal from its sealed response rows. Each endpoint changes exactly one
public history, has a frozen full-policy digest, and is built before the target
selector is called.

`exact_selector_window_oracle` and `exact_selector_fan` are finite-game
evidence primitives. The former independently computes Fraction-exact local
action values, maximizing sets, fixed-tape values, and profile utilities. The
latter linearly interpolates one player's sequence-form realization, derives
rational optimality cells for selected response tapes, and partitions each
section into `fixed`, `tie_unresolved`, and `switched` regions. Exact tie
interval measure and boundary points are retained separately. Complete total-
function identity is conservative certificate semantics; reachable-support
identity is behavioral reporting only, so an upstream repeated-actor switch
cannot silently turn dead downstream entries into a certificate fact.

`selector_window` adds the corresponding Float64 fixed-tape scores and a
conservative margin-reserved window. Zero allowance must reproduce the exact
legacy margin-over-closing-slope breakpoint; a positive allowance may only
retreat. `legal_responder_raise_h4_selector_window` is ADR-0350's prospective
one-shot owner. On four frozen downstream-relevant rays and a 17-point dyadic
schedule it compares exactly 136 production selector calls with the Fraction
fan, rebinds fixed-tape affine gain rows to the maximum upper envelope and
master epigraph direction `z >= row`, and retains both tape identities. It is
not connected to the Legal Decision Spine and emits no action, full-width
result, strategy label, or quality row.

ADR-0351 closes that prospective owner after its sole invocation. The exact
fan map remains retained evidence, but the recorded certificate gate and
integration authorization are rejected. `legal_responder_raise_h4_selector_fan_result`
is the standard-library-only owner: it rehashes the complete ADR-0350 closure
and rebinds rational fan partitions, total tapes, scheduled production tapes,
affine row algebra, maximum envelopes, total/current-reachable identity
arithmetic, controls, payload bytes, and walls. Source-reachable-only fields
are authenticated rather than independently rederived because v1 omitted the
pointwise pruned source tape. It then applies the corrected semantic rule and reports four
reachable source-tie/nonzero-window violations. It imports no runner, game,
evaluator, selector, optimizer, action, or write path.

The original `selector_window` conservative helper is closed for artifact
provenance. Its order was wrong for certificate semantics: it inspected a
nonclosing slope after observing a zero source margin and could leave the
default window at one. `selector_window_v2` makes source separation strictly
outside the semantic reserve a prerequisite. A tie or reserve overlap returns
zero before slope is examined. Future tie-aware integration must retain every
exactly active affine row under the maximum envelope; v2 may certify one tape
only when every source comparison clears that prerequisite.

ADR-0352 adds the source-sealed recovery without changing the closed v1
lineage. `exact_tie_aware_affine_envelope` enriches each exact normal-fan
section with the bounded Cartesian closure of local Fraction maximizers at
every boundary and open-cell witness. Every resulting complete tape is
re-evaluated under its own fixed continuation. Its source/endpoint values
become one exact affine gain row; every active row must equal the exact gain,
all rows must lie below it, and their maximum must reproduce it. Affine-
equivalent tapes remain separate members of the active set.

`tie_aware_affine_adapter` is a typed dispatcher. An exact singleton may use
`selector_window_v2`; a singleton inside the numerical reserve rejects; and
an exact tied source can use only the complete maximum-row envelope after all
of its v2 windows return zero. `legal_responder_raise_h4_tie_aware_affine` is
the prospective exclusive owner. It makes no production best-response call,
serializes both source and current reachable-pruned tapes for every identity
pair, and independently checks `z >= row`. The h4 result path remains absent.
Its eventual same-fixture result can be development integration only, not
untouched confirmation or a production consumer claim.

ADR-0353 closes that prospective owner after its sole invocation. The exact
active-tape enumerator crossed the frozen per-sample bound of 256 before a
completed h4 section or affine row was serialized. The 961-byte artifact is
owned only by `legal_responder_raise_h4_tie_aware_affine_result`, a standard-
library rebinder that imports no runner, oracle, game, evaluator, optimizer,
action, clock, or write path. The literal Cartesian representation is rejected
for this integration; the Fraction oracle, v2 rule, and maximum-envelope
direction remain synthetic mechanism evidence rather than target results.

The next representation boundary is factorized. It must retain an exact total-
function choice-set identity and arbitrary-precision cardinality without
materializing every tape, derive reachable-support identity only as a separate
projection, and quotient equal affine rows while preserving each class's exact
membership/cardinality. Exhaustive small controls remain the oracle for that
quotient, and a distinct-row/compact-state bound must fail before truncation.
No h4 target diagnostic is authorized by the rejection itself.

ADR-0354 implements and source-seals that boundary as a directional calculus.
`exact_directional_face_oracle` builds one bounded explicit finite tree and
runs two independent exact lexicographic backward passes over the factorized
local-maximizer face: both maximize response value, while separate selections
minimize and maximize directional slope. It reports total-function and
reachable-support cardinalities independently, uses arbitrary-precision
integers, and records a linear logical-operation ledger plus the cardinality
bit lengths; no response-tape product is materialized. The point oracle cannot
locate later basis changes, so `compose_exact_directional_face_fan_section`
retains `exact_selector_fan` as the ray authority and checks every boundary,
open-cell row, and future-crossing seam. The 256 bound in that composition is
a fan-piece guard, not a face-cardinality limit. A mechanical
`tie_semantics_conformance` registry applies source-tie, positive-measure,
future-crossing, repeated-actor identity, and high-cardinality controls to
every named consumer. The legacy Cartesian envelope is used only on bounded
synthetic controls. No legal h4 value or result path is opened by this source
seal.

ADR-0355 adds the prospective legal h4 diagnostic around that source without
opening it. `legal_responder_raise_h4_directional_face` reconstructs the
retained h4 fixture and four selector-free directions, composes the exact fan
and face for both target players, and separately evaluates 136 scheduled
point faces. The artifact schema carries complete fan geometry, active factors,
dual cardinalities, slope extrema, factor digests, logical work and bigint bit
lengths. A strict single-snapshot config loader, clean-Git precondition,
exclusive result creation, and result-byte terminal surround the subject. No
target cardinality or geometry is frozen as a gate. The public ADR-0352 runner
remains absent from the call graph, and the prospective result path remains
absent until the committed one-shot invocation.

ADR-0356 closes that owner and installs
`legal_responder_raise_h4_directional_face_result` as the read-only authority.
It imports no scientific or write path and reconstructs exact Fractions,
factor and reachable-support dynamic programs, two tape projections, 147,418
logical work units, fan partitions, tie states, maximum envelopes, schedule
locations, nested digests, aggregates and gates. The retained artifact exposes
a 104,976-member total face with reachable cardinality one and zero tape
materialization. The result owner is not connected to the action path; a new
source-sealed integration consumer must be preregistered separately.

ADR-0357 adds `factorized_tie_aware_affine` as that reusable consumer but does
not open its h4 target. It accepts only an already-composed
`ExactDirectionalFaceFanSection`: the fan locates every ray piece, while the
point face preserves the complete active factor set and directional slope
interval. The adapter rederives total and reachable cardinalities, validates
continuous convex pieces and the exact maximum epigraph, and uses one-sided
inward slopes at domain endpoints. Its modes are nominal: exact source ties
use the factorized envelope with no fixed-tape score call; exact singletons
use selector-window v2 or fail closed. `tie_semantics_conformance_v2` extends
the sealed historical registry without editing it. No Cartesian enumerator or
closed ADR-0352/ADR-0355 owner appears in the new call graph.

ADR-0358 surrounds that reusable source with
`legal_responder_raise_h4_factorized_affine`, a prospective one-shot laboratory
owner disconnected from the action path. It reconstructs the four inherited
directions and both target players, performs exactly eight live adapter builds,
and requires each newly serialized section to reproduce the retained ADR-0356
section digest. Its integration records preserve source-face factors, dual
cardinalities, fan pieces and points, exact maximum-epigraph orientation,
typed singleton/tie dispatch, and a logical work ledger with zero materialized
tapes. Module-level controls exclude both closed owners and Cartesian products.
The target emits no action, strategy label, or quality row; a retained pass can
only motivate a separately sealed untouched confirmation.

ADR-0359 closes that writer and installs
`legal_responder_raise_h4_factorized_affine_result` as a standard-library,
read-only authority. It reconstructs the source factor graph and reachable
quotient, reduced Fraction algebra, logical work, compact convex envelope,
point gains, crossings, inward endpoint and interior seams, typed dispatch,
parent identities, aggregates, walls, claims and gates. The retained schema
contains 12 fan rows but only ten interval-owning envelope pieces: two rows are
endpoint-only. Because raw non-source factors and the two non-quotient rows
were not serialized, their internals and the live reproduced-section digest
remain source-authenticated rather than independently reconstructed. A future
confirmation artifact must serialize every factor and row to remove that
authority limit.

ADR-0360 adds the value-unopened
`legal_h4_factorized_affine_confirmation_population` boundary. It derives four
ordered collision-free card/range contexts only from the clean pre-result
mechanism commit, uses exact dyadic 4-by-4 joint mass and the established legal
checked-to responder-raise tree, and constructs context-bound full-support
source policies without calling a value owner. Its semantic identity reduces
probabilities before comparison, so an unreduced numerator/denominator pair
cannot masquerade as a new context. The sealed successor graph is population
then exclusive direction generation (three DCFR history vertices plus one
audited row-growth proposal) then 32 factorized fan/face sections. Its artifact
schema carries the complete section rather than summaries: every fan row,
every point face and information-set factor, every compact piece, and every
fan-row/point epigraph residual. ADR-0360 itself adds no confirmation runner or
result.

ADR-0361 adds the exclusive
`legal_h4_factorized_affine_confirmation` owner while leaving its result path
absent. Direction endpoints are generated only inside that terminal; the
row-growth proposal is admitted only after independent exact response-row,
evaluation, cap, feasibility, convergence and master-certificate checks. The
`complete_factorized_affine_evidence` boundary serializes the complete fan,
all source and non-source faces, compact pieces, selector-window record and
the full exact row-by-point residual matrix. Total-function identity remains
certificate authority, reachable support remains reporting-only, and the
owner statically excludes the closed ADR-0358 result line and Cartesian tape
enumeration. Dirty source stops before target work and `O_EXCL` plus `fsync`
retains only the first pass, scientific rejection, typed failure,
infrastructure failure or byte-bound terminal. No fresh target has been opened
at this architecture checkpoint.

ADR-0362 retains the sole terminal from that owner without modifying its
recorded rejection. The new
`legal_h4_factorized_affine_confirmation_result` boundary is standard-library,
read-only, and byte-bound. It reconstructs every serialized source/non-source
factor graph, total and reachable cardinality, exact fan partition, affine row,
point-face seam, epigraph residual, compact convex piece, work ledger,
row-growth audit, coordinate, aggregate, and gate. It exposes recorded and
artifact-only corrected gate vectors as different types. The correction shows
that all four emission fields are zero/null and that the sealed writer's
mapping-to-mapping-to-Boolean chained comparison necessarily returned false;
it never rewrites `passed` or the decision in the retained artifact. An AST
control makes the consumed writer the sole named mapping-literal comparison
chain and rejects any new instance. Game-derived live coefficients,
selector-window input score tables, and live timing reexecution remain
authenticated to the sealed source. The accepted conclusion is fresh finite
h4 factorized-affine mechanism evidence only.

`sizing_power_diagnostic` is the parked candidate-blind ADR-0295/0296
successor. It can generate sealed structural pools and compare only full
integer with minimum/all-in values. Its owned qualification runner returns a
batch-bound immutable prefix and stops inside the value-opening function at
target, exhaustion, or ambiguity. Panel extraction rebinds that prefix to the
structural pool before producing a qualified panel. The second replication
still misses its power target, so this machinery is a process/evaluation oracle
rather than a v3 panel source.

`width_four_sizing_power` is ADR-0297/0298's value-free structural successor.
It expands both exact private-hand axes to four, enforces the frozen richer
sign-pattern filter, binds three 96-context pools, and exposes analytic compact-
LP dimensions. It deliberately has no sizing-solver import; value opening must
live behind the separately owned ADR-0297 runner after the structural commit.

`width_four_sizing_power_evaluation` is that owned ADR-0299 boundary. It fixes
all numerical semantics and pivot limits internally, binds each observation to
the sealed pool and analytic dimensions, stops each batch and the campaign
inside the value owner, and runs bounded teacher controls only for completed
panels. The underlying reduced oracle now exposes chip-valued lower-envelope
constraint violation separately from its legacy mixed-coordinate diagnostic.
The passed panels remain development evidence and are not candidate sources.

`reference_hand_replay` joins those boundaries for one controlled seat. Frozen
opponent events, public-card reveal and validation, blueprint key/lookup,
legality, controlled emission, betting transitions, and card-domain audits have
named charged intervals. The explicit full deal remains inside replay/showdown
oracle scope and never enters a blueprint key. Post-terminal evaluator and
settlement verification are reported separately from decision time.

The complete explicit-deal reference hand loop now carries symbolic collision-
aware five-opponent ranges and rational public-action updates. It is still not
a complete agent or solver. Calibrated ranges, scalable full-width contraction,
a trained full-game blueprint, action abstraction, and resolver candidates
remain external. The older river games retain their intentionally restricted
trees as sealed exact research workloads and are not silently upgraded by this
layer.

## Current h32 execution spine

The active boundary is a prepared six-player river decision with 32 hands per
seat. Off-clock preparation builds the immutable blueprint, factorized belief
contexts, shared public topology, resident solver state, and incremental
response caches. Allocator scratch is trimmed before the street becomes ready.

ADR-0307 now governs live time: every controlled action receives one continuous
15,000 ms response wall, including the one-second emission reserve. The clock
starts when the controlled seat becomes the actor and does not pause through
emission. Earlier-street and opponent-turn work is separately measured online
preparation; only an exact provenance-bound artifact hit can be credited to a
decision, and no credit enlarges the response remainder. The additive action-
clock ledger, preparation bank, and exact-spine v2 are implemented and accepted
by ADR-0308. The exact spine derives the active public-state digest, starts at
the event boundary, rejects construction after an unowned live boundary, and
falls back on cutoff or deadline crossing. The old cumulative-street controller
remains a reproduction oracle rather than the governing timing path; the new
spine is not yet connected to the complete-hand replay or a live host.

Inside the 15-second boundary, the frozen systems control performs one resident
warm step, constructs deterministic source-relative candidate deltas, and runs
only independent exact certificates that can finish before a one-second
emission reserve. A candidate may replace the blueprint only if every per-seat
deviation cap and the incumbent NashConv objective pass against that same
immutable anchor. Atomic certificates do not compose; a union is a new policy
and requires exact recertification. Missing, stopped, stale, or late evidence
emits the blueprint.

```text
prepared immutable state
    -> one resident warm step
    -> one retained regret-vertex direction family
    -> complete 31-block continuation affine screen
    -> one deadline-admitted exact winner certificate
    -> certified incumbent or immutable blueprint
    -> reserved synchronization/action emission
```

Continuation rooting is now the active execution shape. It preserves exact
terminal semantics while removing five sixths of strategic nodes, and it makes
all 31 legal changed-public-node blocks affordable inside the street ledger.
[ADR-0228](docs/decisions/ADR-0228-continuation-root-delivers-exact-safe-value-on-all-twelve-targets.md)
records positive exact certified value on all 12 opened posterior targets;
[ADR-0230](docs/decisions/ADR-0230-two-continuation-steps-fit-the-conservative-street-ledger.md)
ledgers. The held-out comparison in
[ADR-0235](docs/decisions/ADR-0235-one-step-retained-after-heldout-depth-value-trial.md)
rejects that affordable second step: 11 of 12 targets reproduce the identical
winner, the remaining target gets worse, and value per charged second falls
13.24%. The active spine therefore retains one step and directs spare time to
generator/action diversity. These are reduced h32 results, not broad poker-
strength claims.

[ADR-0237](docs/decisions/ADR-0237-full-bisector-library-does-not-fit-every-street.md)
keeps that direction width fixed. A second, structurally distinct 31-block
soft/regret bisector family fits 8 of 12 retained street ledgers but reaches
19.42 seconds on the tightest target. No bisector value labels were opened;
memory remained safe and affine work, not residency, is the blocker.

Every successor runner derives acceptance guards and quality normalization
from `layout.game.payoff_span` through `payoff_semantics`; stack is never a
span. Artifact loading, pass-bit access, environment assembly, gate plumbing,
and finite serialization use the byte-pinned `runner_harness`. Active campaign
admission uses its separate `campaign_deadline` successor so historical
provenance remains exact. One `MonotonicCampaignDeadline` spans each bounded
campaign: it checkpoints before every frozen target or arm, requires the entire
unit bound to fit, and
stops immediately after a unit or campaign overrun. Campaign time remains
separate from the shared 15-second street ledger. Byte-pinned historical runners
remain immutable, with their legacy expressions held in an exact AST exception
inventory. New device-fold customers likewise use the non-consuming,
contiguity-guarded `resident_record_to_hand_fold_v2` successor rather than
altering the pinned fold. Its validated host Int32 topology mapping is the sole
hand-index authority; the device copy is constructed internally after seat and
range checks. [ADR-0233](docs/decisions/ADR-0233-shared-payoff-semantics-and-runner-contracts-retire-repeat-defects.md)
is the governing process correction.

GPU semantic equality is numerical under preregistered Float64 ceilings; exact
digests remain authoritative for immutable provenance and explicitly bitwise
questions. [ADR-0166](docs/decisions/ADR-0166-prepared-street-fits-two-atomic-certificates-after-one-warm-step.md)
closes the present systems-capacity spine, while
[ADR-0178](docs/decisions/ADR-0178-regret-vertices-expose-soft-generator-weakness-but-not-a-live-selector.md)
shows that candidate generation—not certification alone—is now the active
strategy research problem. The 8/32/64 ladder in
[ADR-0184](docs/decisions/ADR-0184-ordinary-deep-dcfr-plateaus-while-purification-remains-direction-sensitive.md)
adds that ordinary depth produces substantially more policy motion without a
material certified-value lift; direction and causal opportunity identification
therefore precede amortized deep solving. The completed causal screen in
[ADR-0186](docs/decisions/ADR-0186-fresh-vertices-replicate-generator-weakness-but-no-free-selector-transfers.md)
keeps that ordering explicit: regret vertices nearly saturate the bounded
three-family oracle, a best-response vertex is redundant, and neither regret
mass nor minimum action gap locates the value. A charged cap-radius probe is a
promising geometric observation but not a free or transferred selector. The
next architecture layer must acquire enough of that information inside the
street before predictive-DCFR variants or wider direction libraries are
justified.

[ADR-0190](docs/decisions/ADR-0190-selector-stable-affine-certificate-is-exact-and-fits-retained-street-ledgers.md)
accepts the first additive implementation of that layer. For a one-seat,
one-public-node direction it contracts the scale-one endpoint once, propagates
affine slopes through the immutable source response tape, and stops before the
first conservative selector tie. It matches the accepted incremental verifier
to `1.36e-15`, preserves that historical verifier byte-for-byte, and fits all
six retained seat-0 street ledgers. The primitive is now eligible for a fresh
deadline-guarded trial, but it remains invalid for multiple changed public
nodes, response-switch intervals, unions, or chained updates.

[ADR-0191](docs/decisions/ADR-0191-preregister-fresh-seat0-selector-stable-affine-street-trial.md)
freezes that first trial as a deliberately nonadaptive runtime slice: one
resident step, one fixed seat-0 regret vertex, one affine proof, and preloaded
blueprint fallback. Two start guards protect the one-second emission reserve.
The old exact verifier is a post-emission teacher only, so it can reject the
trial but cannot choose its live action.

[ADR-0192](docs/decisions/ADR-0192-fixed-seat0-affine-rule-emits-four-fresh-certified-candidates-before-deadline.md)
shows that slice closing prospectively: all four fresh seat-0 trials emit a
certified candidate before the cutoff, with exact teachers agreeing to machine
precision and at least 3.80 seconds of boundary headroom. Value varies by 565x,
so the architecture keeps acquisition correctness separate from opportunity
magnitude and next tests the unchanged mechanism at acting seat 5.

[ADR-0193](docs/decisions/ADR-0193-preregister-fresh-seat5-affine-street-replication.md)
freezes that replication as a hash-bound successor of the seat-0 live core.
Only fresh target seat 4 and fixed acting seat 5 change; all proof, deadline,
fallback, and post-emission teacher semantics remain identical.

[ADR-0194](docs/decisions/ADR-0194-affine-street-mechanism-transfers-to-seat5-but-value-remains-concentrated.md)
confirms the transfer: seat 5 also completes four of four fresh candidates on
time with machine-precision exact teachers. Across both extremes, however, two
targets carry 88.78% of value. The architecture therefore treats the affine
runtime as provisionally sound and moves the research boundary to causal
materiality and broader position/belief coverage.

[ADR-0195](docs/decisions/ADR-0195-preregister-read-only-h32-resident-step-bottleneck-profile.md)
opens a separate compute-time subgate without consuming a fresh strategy
context. It replays the disclosed fastest and slowest seat-5 targets and
partitions the dominant resident step into device, transfer, host-fold, and
residual buckets. Its Amdahl estimates can route the next engineering screen;
they cannot justify a hardware purchase without a workload-specific follow-up
or weaken the 15-second fail-closed boundary. Its first invocation rejected
before replay on a parent-schema lookup; the additive
[ADR-0197](docs/decisions/ADR-0197-preregister-source-schema-corrected-resident-step-profile.md)
changes only that lookup and preserves the timing protocol.

[ADR-0198](docs/decisions/ADR-0198-device-pipeline-dominates-h32-step-host-fold-is-second.md)
accepts the corrected attribution. The resident GPU pipeline owns 67.87% of
pooled step time, host record-to-hand folding 30.56%, and transfers only 0.63%.
The runtime therefore profiles device arithmetic versus bandwidth first and
keeps a resident hand reduction as the secondary optimization. Candidate
portfolio capacity remains deadline-derived; neither median timing nor a
standalone proof bill may choose K.

[ADR-0199](docs/decisions/ADR-0199-preregister-retained-affine-selector-cascade-replay.md)
freezes the next no-new-label selector layer. It extracts the same exact
Tier-A/Tier-B affine features for all 108 already labelled block-direction
rows before semantically loading the labels, prices K from measured work, and
scores the primary six regret vertices separately from the confounded 18-row
family library and its soft-excluded control. The primary set is explicitly
library-limited if K reaches six; pooled or family-discrimination performance
cannot be presented as a live selector result. Its first invocation rejected
at final aggregation on a memory-field spelling; the additive
[ADR-0201](docs/decisions/ADR-0201-preregister-memory-schema-corrected-selector-replay.md)
then rejected its legitimate four-field source as an overstrict two-field
schema. [ADR-0203](docs/decisions/ADR-0203-preregister-final-four-field-selector-replay-correction.md)
pins all four source fields, adds only the exact `gpu_free_bytes` alias, and
recomputes the full matrix. That wrapper later rejected on the reporting API,
so [ADR-0205](docs/decisions/ADR-0205-preregister-reviewed-direct-selector-replay.md)
closes the wrapper line and freezes a direct orchestration: raw four-field
memory consumption, zero-argument environment metadata, pre-write JSON
serialization, and the unchanged ADR-0199 scientific helpers.

## Architecture evolution record

The narrative below records how the architecture reached the current spine and
is retained for mechanism provenance. Words such as “current” and “next” in
that record are time-scoped to the experiment being discussed; use generated
[STATUS.md](STATUS.md) for the live decision.

The Python package implements `game-core`, `exact-lab`, the reference portion
of `solver-core`, and a small experimental public-belief/online-search control.
The Bayesian continual compositor is a rejected negative control, not the
production resolver. `safe_resolving` is the exact two-player correctness
control: its chance root uses chance × resolver reach, its opponent opt-out
information sets carry blueprint counterfactual-best-response values, and only
the resolver component is exported. Its full-game target remains outside
policy construction. Performance backends and future approximate gadgets must
remain differentially testable against this implementation.

The safe frontier interface is vector-valued. Each opponent augmented root
information set has counterfactual reach, blueprint CBR value, candidate CBR
value, and positive violation. Finite-solver error is a first-class certificate,
not an unreported convergence assumption. Exact best-response certification is
permitted only in the laboratory; a scalable system will need conservative
value bounds or a permanent no-op fallback.

`maxmargin` adds an exponential exact-strategy oracle around that frontier. It
enumerates pure subgame plans, solves max-min and constrained objectives, and
checks mixed-to-behavioral realization equivalence against dynamic best
responses. The target-free sum-margin LP is the current teacher objective. A
second LP may inspect the full-game opponent best response only as a hidden
diagnostic control; it is explicitly outside the online dependency graph.

`safe_solver_gap_experiment` treats search as an anytime stream. The blueprint
is the initial incumbent; average and current snapshots must pass every exact
frontier constraint and improve the target-free summed margin before replacing
it. This exact monitor is a teacher interface, not runtime certification. A
frozen fixed-regret-mass rule failed holdout transfer, so the next solver layer
must represent feasibility constraints and secondary objective progress
directly rather than relying on gadget Nash convergence to select a policy.

`constrained_generation` is that direct exact-lab control. Its restricted LP
starts with the complete behavioral blueprint, adds opponent counterfactual
best-response rows on demand, and uses LP duals to construct one weighted game
whose dynamic resolver best response prices the best missing column. It never
enumerates the resolver normal form during construction. A monotone incumbent
exports only an independently frontier-feasible policy with larger summed
margin. Exact normal-form and complete-game oracles remain excluded teachers.
The current reference profile says separation and pricing traversals, not the
small simplex, are the first optimized-kernel targets.

The frozen five-update rule missed the fresh holdout rate gate despite passing
safety, exactness, capture, and screen-to-holdout transfer gates. Its round
layout prices a future column after the current incumbent is already known; a
fixed deadline can therefore pay for work that cannot improve its returned
policy. Future implementations must expose phase-level cancellation points and
distinguish quality-producing separation from future-option pricing.

Phase v2 makes that distinction executable. Candidate-ready time ends after
one behavioral-policy safety separation and before current-round pricing.
Duplicate response and realization audits remain available as reference flags
but are not charged to v2; exact teacher comparisons remain outside candidate
construction. Terminal cancellation returns the safe incumbent without
creating a column that only a later master could consume.

The phase-v2 holdout shows why the scheduler boundary belongs above the solver.
Conditional solver efficiency transfers and beats CFR strongly, while absolute
margin/ms falls when blueprints contain less safe-improvement headroom. The
runtime needs a target-free opportunity estimate alongside phase cost; low-
opportunity decisions should retain the immediate blueprint and release their
budget to current or speculative jobs with higher expected value.

`opportunity_trace` now enforces the scheduler's causal interface. A boundary-
start decision sees only public context; a candidate-ready decision may inspect
the solved master and its one paid safety separation but cannot inspect current
pricing; a post-pricing decision may inspect the purchased reduced-cost option.
Exact objectives and future improvements exist only in the training-label
plane. Allocation controls scope reusable compute to states sharing one fixed
blueprint, while cross-blueprint pooling remains a deliberately loose
diagnostic.

Solver work is not assumed to produce reward every phase. In the exact traces,
useful columns and response constraints often require several alternating
cycles before the safe incumbent moves. The scheduler must therefore rank
preemptible macro-options with intermediate cached state, rather than kill any
job whose immediately following candidate has zero gain. Current early scalar
features do not predict that option value well enough in Kuhn. ADR-0021 moves
that interface into an exact full-deck river microgame. `river` owns cards,
showdowns, joint combo beliefs, and fixed bet/raise state machines;
`river_oracle` independently solves its normal form; `river_context` creates
board-grouped range families; and `river_opportunity` records causal regret and
policy traces against hidden exact labels. `river_trace_analysis` compactly
audits signal ranks, paid-probe allocation ceilings, and solver paths without
fitting. `river_trace_comparison` verifies exact board/range pairing before
measuring cross-tree transfer.

ADR-0022 records the sequential result. Adding one raise and final response
breaks the local-regret/NashConv identity, but also reduces accumulated regret's
correlation with the relevant gain-per-work target to a moderate level. State
visits are the stable development cost and serial solver milliseconds are the
required runtime replicate. Any scheduler using checkpoint-two features must
first charge every job for that probe. Static one-bet difficulty rankings do not
transfer to the exactly paired raise tree, so tree-local online measurements,
not a cross-abstraction hardness cache, drive the next transparent screen.

`river_shadow_probe` applies alternate numerical regret updates to deltas
already produced by DCFR. The shadow never selects traversal behavior or walks
the tree again, and paired instrumentation must leave every active accumulator
unchanged. The development screen found its extra signal too redundant to pay
for: shadow and active raw-regret ranks correlate at `0.978`. The frozen
`river-post-probe-scheduler-v1` therefore keeps only a one-pass active positive-
regret summary. `river_scheduler_screen` ranks a shared pool after checkpoint
two and funds a bounded number of checkpoint-six jobs by stopping low-ranked
jobs at checkpoint two. Its budget ledger covers both iterations and
deterministic state visits; fixed checkpoint-four DCFR remains the no-feature
fallback. This is a speculative-job allocation interface, not permission to
transfer compute between unrelated completed poker decisions.

`river_scheduler_holdout` is the reserved-evidence boundary. It accepts one
hard-hashed rule, performs no candidate selection, ranks and balances work
independently inside board-group folds, and charges the separately timed regret
summary plus allocation. A passing validation artifact with the identical rule
hash is required before test evaluation. The frozen rule passed both stages;
its sealed-test charged reduction/ms advantage is 2.499%. It is therefore the
control for richer search experiments, while fixed checkpoint-four remains the
fallback outside this exact sequential-river workload.

River cache identity has two levels. `structural_digest` covers the public board
and betting structure and may key immutable topology or showdown work.
`provenance_digest` adds the entire normalized joint range and is required for
an exact deployable strategy hit. Approximate belief matches never cross that
boundary: they may seed a solver, but the candidate must be recomputed or
recertified under the current joint range. Root total variation bounds only the
value of a fixed policy and does not imply conditional-range, best-response, or
equilibrium stability.

`river_cache` enforces that boundary in code. A structural match may return a
defensive nondeployable policy hint and cached information-set/action schema;
only exact provenance returns a deployable strategy. For this two-player zero-
sum game, a separately certified source exploitability extends the TV argument:
the same fixed policy's target exploitability is at most source exploitability
plus `2 * payoff_span * joint_TV`. This is a conservative policy-quality bound,
not a range hit or strategy-distance guarantee, and it does not extend to
multiplayer.

The blocker-sensitive screen makes recertification the next cache subsystem.
Exact-source policies remain excellent after a 1% root shift even when local
equilibrium-policy TV reaches one; solving them further is worse on average than
deploying them after exact current-range recertification. The global TV bound is
cheap but too loose.

`river_incremental` now implements the exact middle path. `RiverRangeDelta`
binds a lossless probability delta to source, target, and structural provenance.
`RiverPolicyEvaluationCache` compiles probability-free per-deal fixed-policy
and counterfactual best-response coefficients. Delta application changes only
the private-hand aggregates touched by reweighted, removed, or added deals and
recomputes their maxima. Added support is compiled under the target game; an
unseen information set uses the fixed policy evaluator's ordinary uniform
fallback. There is no approximate-hit threshold or unchecked chained update.

This specialized evaluator is a reference control, not the final cache engine.
Its finite-policy benchmark is exact and fast even when every delta scan is
charged separately, but its best-response dependency graph has only two layers
and its production changes touch two explicit deals. The next cache interface
now exists as `dependency_tape`. It compiles any supported root-chance game and
fixed policy into topologically ordered Float64 arithmetic arrays. Reverse CSR
dependencies drive sparse invalidation; a dense mode sweeps every arithmetic
node. Information-set argmax nodes choose one global best-response action while
history-select nodes preserve imperfect information. A declared support union
allows source-zero outcomes, and every target is evaluated through an
epoch-stamped overlay relative to immutable source values.

The generic tape matches the full evaluator and specialized river control on
finite policies, unseen-hand additions, dense likelihood changes, and actual
selector flips. It remains an exact reference layout, not a deployment kernel:
Python wall time mixes compilation and redundant controls, while an explicitly
enumerated joint outcome universe will not scale directly to six players.
Multiple bet/raise sizes are the first branching-factor transfer gate. Full
evaluation remains the independent differential oracle; structured dense range
algebra is the likely complement to sparse explicit invalidation.

`river_multi_size` now supplies that transfer workload without altering the
fixed-size game. Opening bets and raise-to totals are immutable sized actions;
legal raises are filtered by the full minimum-raise rule, every contribution
fits both stacks, information keys retain exact public sizes, and joint-range
provenance remains separate from topology. `river_multi_size_audit` independently
reconstructs utilities from committed contributions and showdown results.

The unchanged tape remains exact on three bets and two raises. This branching
expands mean numeric topology `2.896x` and flat bytes `2.985x`. Sparse dirty
fractions decrease slightly, but absolute dirty work rises `2.69x`-`2.73x`.
Accordingly, the architecture treats the 3x2 tree as a reference action universe
rather than a chosen abstraction. The next layer must preserve a complete 3x2
blueprint while masking search actions, so every candidate—including off-tree
responses—is evaluated in one common full game. Only action sizes that improve
full-universe quality per charged work advance to branch-major SIMD layout.

`selective_tree` implements that layer without deleting legal actions. Every
reached information set retains the full action tuple. Selected nonterminal
branches expand normally; unselected branches become fixed-blueprint
continuation leaves. `river_selective` binds that generic mechanism to exact
sized bet and raise actions and composes a complete deployment policy by
replacing only materialized information sets. A zero overlay is exactly the
blueprint, and full expansion is tested against the unwrapped solver.

The first pilot rejects a premature native layout decision. Partial masks use
38%-79% of full tree states, but the full mask is the best fixed arm at the
first positive aggregate budget. A fixed-warm, per-target mask/no-op oracle has
11.43% more reduction than the corresponding full-mask/no-op oracle, so the
architecture retains mask choice as a scheduler option rather than a fixed
abstraction. Exact future labels define this ceiling only; causal features and
stronger group-separated blueprints are required before deployment or C++
specialization.

The group-separated matrix confirms the opportunity but sharpens the runtime
boundary. At 32 full-tree-equivalent iterations, exact best-mask/no-op is 13.61%
above full-mask/no-op and every development board group is positive. Yet full
expansion remains the best fixed arm in every held-out-group control, and the
two shallowest selective solves become more harmful with additional
iterations. The runtime therefore needs three distinct decisions: whether to
search, how wide to search, and whether to accept the result. Exact continuation
leaves solve none of those decisions by themselves. Cheap range-delta geometry
is evaluated before blueprint-public traversal or a paid solve; all feature and
recertification costs remain explicit. Native branch-major specialization waits
for a causal no-op/near-full/full rule to beat always-full without future-label
access.

That compact causal rule does not pass. Group-held-out trees can trade pot-
normalized quality for raw chips and lower work, but no preregistered candidate
beats fixed full search on normalized quality; the closest improves only four
of eleven groups. The runtime therefore retains the full action lattice and
drops adaptive-width specialization for this workload. The unresolved control
moves to acceptance: a parameterized dependency tape should ingest candidate
policy-probability deltas, propagate only their exact affected cones, and decide
whether the full candidate improves the incumbent. Exact acceptance is a
heads-up teacher and must not be called multiplayer-safe.

## Reduced-h32 one-seat convex generation

The current multiplayer direction generator no longer searches only isolated
regret rays. On a compiled continuation where no root-to-terminal path visits
two information sets of the same seat, the acting seat's full behavioral axis
is affine. `behavioral_open_axis` contracts exact profile and fixed-response
rows, while `behavioral_one_seat_master` minimizes six deviation-gain epigraphs
over every information set of that seat. General repeated-actor continuations
must use sequence form; the behavioral shortcut fails closed at layout compile.

An exact all-seat response oracle separates the restricted master. Newly
exposed opponent response signatures add exact rows; already-resident rows are
accepted only when they reproduce the oracle and remain inside the verified LP
primal ceiling. The 15-second ledger currently permits at most one multi-cut
round. Because that bounded master need not be fully separated, it carries no
global-optimality claim and is never the safety authority.

Historical v1 masters retain their sealed primal-objective telemetry, but that
quantity is not a mathematical lower bound. Successors use
`behavioral_one_seat_master_v2` or the sequence-form adapter in
`linear_program_certificate`: solver multipliers are projected to valid signs,
the residual is minimized over proved variable bounds, and Float64 arithmetic
is rounded outward. Raw primal and dual objectives remain diagnostics; only the
certificate may be called `L` or used in `U - L`.

The deployable unit is a fixed factor-`0.5` blueprint retreat followed by an
independent exact all-seat certificate. Acceptance requires exact per-seat cap
feasibility, positive NashConv improvement, restored interior slack, and both
measured and conservative street ledgers; otherwise the immutable blueprint is
the outcome. Multi-seat edits, chaining, cross-street reuse, and banked guard
remain outside the contract.

[ADR-0258](docs/decisions/ADR-0258-convex-half-retreat-delivers-material-value-on-all-six-latin-e-targets.md)
is the first breadth result for this layer: all six label-blind Latin-E
half-retreats are exact-cap-safe, materially positive, and within the full
ledger. The development runner freezes every campaign candidate before opening
final labels and reconstructs certificate contexts one at a time to respect GPU
memory. The untouched confirmation in
[ADR-0260](docs/decisions/ADR-0260-latin-f-confirms-convex-breadth-with-two-interior-abstentions.md)
passes at four of six: all six raw retreats are positive and exact-cap-feasible,
but two correctly abstain because their slack misses the stronger interior
floor. Across both panels, ten of twelve deliver under the full contract. This
authorizes prospective live-shadow integration with the same no-op path; it
does not infer an IID population rate or a fresh comparison against the one-
step regret-vertex fallback.

[ADR-0262](docs/decisions/ADR-0262-post-call-panel-is-fresh-current-and-nondegenerate.md)
aligns that next integration with the actual decision root. After checks, a
bet, and the first responder's call, the second responder is both the declared
one-seat axis and the current fold/call player; three opponents remain
downstream. The complete current-decision axis is therefore one public node,
32 h32 information sets, and 64 behavioral variables. Six fixed post-call
posterior identities pass the label-blind freshness, topology, and belief-
nondegeneracy gates.

[ADR-0264](docs/decisions/ADR-0264-current-decision-convex-shadow-delivers-six-safe-candidates-in-five-seconds.md)
opens those labels prospectively. All six half-retreats are exact-cap-safe,
interior, positive, and shadow-accepted; four exceed `0.001`, both range
families are represented, and the maximum measured live ledger is 5.081
seconds under the unchanged 13.968-second conservative floor. The setup adapter
is scoped and restored, and the actual emitted policy remains the blueprint.
This authorizes a post-fold identity test, not deployment.

[ADR-0266](docs/decisions/ADR-0266-post-fold-panel-is-fresh-current-and-held-label-blind.md)
seals the complementary six post-fold identities. They preserve the same
current-player, one-node h32 axis, and three-opponent downstream geometry while
changing only the first observed response from call to fold. Their strategy
labels remain closed pending an off-clock full-convergence census on
already-opened contexts. That census distinguishes finite global one-seat
solvability from the current live engine's one-cut-round guarantee; the latter
continues to certify only the emitted retreat, not global optimality.

[ADR-0270](docs/decisions/ADR-0270-current-decision-programs-close-wide-axis-census-does-not.md)
measures that distinction across all 42 opened compatible contexts. Thirty-
five programs close globally in zero to three exact multi-cut rounds, six
reach no-new-facet states whose LP points still fail the tighter exact cap, and
one wide-axis master hits its KKT verification guard. Only 18 of 42 close by
round one, so the broad live path retains its direction fallback. In contrast,
all six actual current-decision programs close in zero or one round (four and
two, respectively). That subgroup authorizes a combined endpoint-closure plus
retreat-certificate ledger replay, not deployment or a global-population
claim.

## Pre-bet row-cache trust boundary

The current authorized cache primitive is the additive CPU v2 control, not the
historical v1 seed path. A factory-built context derives the complete numeric
layout, game, belief, action schema, policy tapes, source payoffs and acting
best response. Population generates its rows only from provenance-bound affine
contexts, and a complete persisted-byte hash binds all rows and the acting
seat's invariant best-response scalar. The writer returns an unsealed record;
lookup can consume the bundle only through a separately persisted seal loaded
under an already expected seal hash. Any miss, v1 file, malformed scalar,
identity mismatch, self-authored writer hash or byte mismatch yields only the
immutable blueprint fallback.

Current-node affine extraction is also explicitly root-only. Typed successor
adjoints bind the complete source tape and numeric layout as well as both the
acting-policy and payoff roles. The context builder independently checks the
source payoff and every coefficient against the dense root oracle; stale,
relabelled, raw and crossed-role results reject. A future nonroot implementation
must represent upstream own realization reach rather than reuse the root
coefficient formula.

Off-clock population, external hash sealing, and live replay remain separate
prospective stages. A future seed runner must use the deadline-owned publisher:
bounded data and completion-seal phases execute while an exclusive lock makes
partial state unconsumable, and lock removal occurs only after both phases and
their campaign checks pass. Failure preserves an unsealed or lock-marked
diagnostic. Consumers accept only a verified canonical-data/seal pair with no
lock. The present dense coefficient oracle is a reduced CPU control and has no
h32 scalability claim; no v2 h32 seed or replay is currently authorized.

## Literal full-width capacity boundary

ADR-0363 adds a pre-allocation authority in front of the current FactorTT
lineage. A live one-seat river belief remains five complete 990-combo opponent
axes conditioned on the known controlled hand. Capacity evaluation inserts
that hand as one singleton so the payoff object has six seat modes in semantic
seat order. The current 3/3 topology recursively stores every compatible
assignment within each half; it may not begin that construction merely because
the compact unary belief itself is small.

`full_width_factor_tt_capacity` derives exact persistent numeric-array bytes
from labeled compatible-half counts, mode widths, fixed dtypes, subset-table
widths, and component count. It separately reports the frozen-order base
topology, the bidirectional open-mode topology, an optimistic scalar ordering,
and the resident belief cache. Those numbers are lower bounds, not peak memory:
Python construction objects, incidence key sets, sparse operators, workspaces,
automata, tensor trains, results, and scratch remain explicitly outside them.

The one-shot owner compares those necessary lower bounds with fixed host/device
numeric caps and live physical reserves before calling a target topology
compiler. Any failed conjunct yields a zero-allocation representation terminal.
Only an admitted target can compile the full current stack, run an internal
scalar differential, prime one resident leaf contraction, and measure one
identical warm contraction. A reduced 12-hand-per-opponent GPU control exercises
that whole operational path and checks the accounting against live object
bytes. The warm unit is intentionally narrower than a CFR iteration, master,
certificate, solve, or complete action, and its 14-second ceiling preserves the
separate one-second action-emission reserve.

This boundary emits no action or quality label. A failure routes work to a new
representation design, but does not select certified truncation or prove that
full-width solving is impossible. A pass would establish only the measured
leaf-contraction scope; the complete full-width river strategy bridge remains
separate.

ADR-0364 closes the v1 owner before this architecture reached its capacity
branch. The first runtime snapshot called the 64-bit Windows process-memory
API through undeclared ctypes signatures and retained
`GetProcessMemoryInfo failed`; no reduced control, allocation record, resource
admission, topology, or contraction appears in the artifact. A typed diagnostic
declaring `HANDLE`, pointer, `DWORD`, and `BOOL` signatures succeeds through
both PSAPI and Kernel32 with the same 80-byte counters structure. The additive
v2 boundary must own that typed ABI and an independent live sanity check while
reusing only hash-bound v1 semantics. The v1 module and result are immutable.

ADR-0365 implements that additive boundary. `windows_process_memory` owns the
declared Win64 structures and signatures, reads both PSAPI and Kernel32, and
cross-checks the same Python PID through hidden no-profile PowerShell. The
512 MiB delta is a sampling-skew gate isolated from all resource and decision
quantities. `full_width_river_capacity_preflight_v2` loads the exact v1 config
through its sealed parser, verifies the exact v1 runner/result and allocation
model, and delegates only the unchanged reduced control and target functions.
It owns new telemetry, Git, protocol, failure, and exclusive-write seams. Its
result path remains absent until the one clean-commit invocation.

ADR-0366 records that invocation's passing guard and rejecting admission. The
literal left half has 733,055,400 compatible three-opponent records; its 64-way
query/source tables dominate storage. Exact persistent numeric lower bounds are
249,485,611,328 bytes for the base topology and 437,433,864,128 bytes
bidirectionally. An optimistic singleton placement still needs
202,627,279,808 bytes, while the resident belief alone needs 14,678,987,408
bytes. All host/device cap and reserve checks reject before allocation, so no
target topology or contraction exists. The replacement architecture must
eliminate card-conflict factors without explicit compatible-half records and
must preserve forward plus reverse/open semantics under reduced exact oracles.
Support truncation is not part of this conclusion.

ADR-0367 preregisters the replacement's first algebra layer. In a directional
pass, all source-half seats must be fully summed; every open private-hand mode
must live on the query/right half. Each target therefore owns a split or seat
permutation that puts it on the query side. After multiplying every
seat-specific unary, mixture-component, and tensor-train factor, labeled
source assignments with the same occupied-card union may be summed losslessly:
cross-half compatibility observes only that union. An open source seat rejects
instead of entering the quotient.

The reference operator stores canonical occupied masks and exact coefficients.
Containment marginals `Z[T] = sum(M superset T, C[M])` answer a query mask `L`
by `sum(T subset L, (-1)^|T| Z[T])`. Reversing source and query is the exact
transpose of this disjointness matrix, not a second compatibility rule. The
fixed controlled hand may be projected out only after proving its cards absent
from every source axis. For the frozen three-opponent/two-opponent variable
split, source masks carry six or four cards and both directions need subset
keys only through cardinality four. The resulting 164,221-key combinatorial
count excludes feature arrays, query records, scratch, automata, tensor trains,
refresh work, and placement, so it is not yet an allocation result.

The first implementation is deliberately a bounded exact CPU differential.
It must reproduce literal compatibility, dense poker enumeration, current
FactorTT/open-mode results, the transpose dot product, bit-identical
three-source-seat permutation, and topology-stable one-seat refresh. It has no
full-width call site. Only after that algebra seal may a separate bound price
all persistent, scratch, cold, and warm work before a GPU keystone.

ADR-0368 seals that reference as `occupied_card_quotient`. Its topology owns
original and projected masks, canonical source occupancies, labeled-to-mask
group IDs, exact multiplicities, and the source/query/open seat contract.
Exact coefficients serialize as numerator/denominator pairs, making the
three-source-seat permutation and topology-stable refresh controls
byte-comparable. The forward operator and record-level transpose share the
same containment/inclusion-exclusion primitive; a work record keeps labeled
source rows, unique masks, marginal visits, labeled queries, signed terms, and
feature width distinct.

The bounded six-seat differential places targets 3, 4, and 5 on the right,
projects one fixed controlled hand only after absence checks, and sums three
closed source seats. Its 630 source records quotient to seven masks at exact
multiplicity 90. Per-hand reach/value rows match dense enumeration and the
current reverse/open `left_to_right` path, while scalar output matches both
existing scalar oracles. Randomized exact rational controls, literal transpose
and dot-product checks, sparse zeros, unsafe projection, and source-open
rejections keep the proof independent of that Float64 fixture.

This module is not deployed. It still stores bounded labeled source records
and its refresh recomputes all coefficients. The next architecture layer must
price a non-enumerative full-width builder, combination indexing, both
directional feature tables, labeled query grouping, scratch, automata, tensor
trains, results, and CPU/GPU placement before a device implementation exists.

ADR-0369 freezes that arithmetic layer before implementation. Each one-seat
pass permutes its open target onto the query/right half, so the concrete
operator always maps six-card source occupancies to labeled four-card query
records. Its reverse is the exact adjoint of that same matrix. It never creates
the invalid fixed-split alternative with a 733,055,400-record open-query axis.

Source occupancies and containment keys use implicit collision-free
combination ranks. Query masks and two labeled hand indices remain explicit.
The proposed device dataflow streams 32,768 source occupancies into one dense
feature chunk, accumulates the global 164,221-row containment table, then
streams 65,536 labeled queries at a time. Source and query scratch phases are
mutually exclusive. The structured showdown automaton is consumed directly;
allocated tensor-train bytes are zero, while the forbidden dense one-hot export
is still priced as an exclusion control.

For each term and mixture component, one column belongs to every state after
the three closed source seats and one to reach. Sunk payoff is an affine fold
of reach rather than a duplicate feature. The frozen fixture expects source
rank 175 and feature width 176; a separate safe hand-axis envelope is 2,971.
Both are arithmetic inputs to a memory model, not throughput evidence. Any
source-seat unary change rebuilds coefficients and containment marginals in
full; only query-only changes may reuse them.

ADR-0370 validates this layout as source arithmetic. The exact reference-hand
state trace is `59/117/175/4/5`, giving 176 state-plus-reach columns. Host peak
is 199,708,580 bytes and the separately priced adjoint sets the 492,448,676-byte
device peak. The safe 2,971-column envelope remains below the fixed gates at
3,184,828,548 host bytes and 8,126,480,964 device bytes. Persistent labeled
source and sparse-incidence storage, plus allocated tensor-train storage, are
all exactly zero.

That byte passage does not settle execution. A source-seat refresh revisits
733,055,400 labeled pairings and performs 81,711,241,920 containment scalar
additions at fixture width; the record-level adjoint can stream
129,017,750,400 label scalar writes. The next architecture boundary is a
prospectively sealed GPU numerical/throughput keystone over the direct
structured automaton. It must preserve the exact bounded oracle and work
counters before any literal full-width target allocation.

ADR-0371 freezes the first device mechanism prospectively. Its forward table
uses the exact cardinality recurrence
`Z_k(T) = sum_x Z_(k+1)(T union x) / (s-k)` and signed subset evaluation;
the adjoint uses the same operator after labeled-query aggregation. Implicit
colex ranks own every row, and deterministic row-feature kernels require no
Float64 atomics or incidence table. The direct showdown automaton constructs
source state-plus-reach coefficients, while query evaluation applies the
remaining transitions and folds sunk payoff from reach.

The only executable population is the complete ten-card reduced universe.
All 45-card row, byte, batch, and work values are pure preallocation arithmetic:
at width 176 the recurrence owns 9,789,072,480 scalar edge additions, and a
128-feature table would own 9,759,784,960 bytes. Neither number is device
evidence. Source changes rebuild all levels; query-only changes may reuse them.
A reject-before-CuPy guard, exact work ledger, independently named Float64
envelopes, warm byte identity, forward/adjoint dot products, and deliberate
recurrence/sign/seam mutations are part of the mechanism boundary.

ADR-0372 seals the implementation on the complete ten-card population. Direct
source coefficients, both recurrence directions, record-level adjoint, query
affine fold, and the current FactorTT normalized chip value match their
independent authorities within the frozen envelopes. Row-feature ownership is
deterministic and source contains neither Float64 atomics nor explicit source-
mask/incidence arrays. A source change rebuilds every coefficient and level;
a query-only change reuses them and reports zero source/recurrence work.

The measured 0.4435/0.2958/0.4346 ms cold/warm/source-refresh device sums are
ten-card CUDA-event units. The 4.679-second conformance wall includes exact
oracles and mutations. Neither is a 45-card, solve, or action wall. The next
architecture boundary is a prospectively frozen non-45-card scaling ladder;
the public keystone itself has no arguments and cannot accept the target.

ADR-0373 freezes the new orchestration layer without changing that sealed
primitive. It generates complete 10/16/22/28/34/40-card axes, a 43-strength-
code direct automaton with source rank 127, and one 128-feature resident batch.
Each stage owns independent cold, warm full rebuild, changed-source full
refresh, query-only reuse, and unique-adjoint phases. Selected direct scans use
implicit colex source rows and bypass the recurrence; the width-128 adjoint
never expands 90 labels but retains their modeled write count.

The staged layer must pre-price all numeric arrays, release memory pools between
stages, repeat live admission, and append/fsync one durable record only after a
stage's numerical, work, allocation, wall, and identity gates close. It stops
on the first typed rejection and is structurally unable to admit 45 cards.

ADR-0374 implements and source-seals that layer. Its pure allocation model
prices the original, source-refresh, and query-only unaries simultaneously
with the mode factors and all phase-specific workspaces; the 40-card peak is
10,046,423,704 bytes before live admission. Cold, warm-full, source-refresh,
query-only, and adjoint counters have distinct semantic field names. The
selected direct oracle launches one thread per query-feature and bypasses the
recurrence. Raw event observations, bit-identity observations, errors, pool
counters, and host walls are serialized so a CuPy-free reader can reconstruct
every gate aggregate and terminal seam. This remains a source architecture:
the real staged journal is absent, and no timing or live-capacity result exists.

ADR-0375 exposes a lifecycle seam outside that scientific architecture. The
sole v1 command reached exclusive writer construction while its frozen
`artifacts/` parent directory was absent. Because writer creation wrapped the
runner's stage-level exception boundary, no header or infrastructure terminal
could be persisted; the call graph proves the stage executor was not reached.
V1 is closed. The next owner must add a tracked hash-bound parent and a new
result identity, validate the literal bootstrap before stage authority, and
inherit the ADR-0373 science without editing the sealed v1 files.

ADR-0376 supplies that additive lifecycle architecture. The repository-owned
artifact marker is both content-hashed and verified as exactly Git-tracked.
V2 validates its literal result/partial parent and the continued absence of
both v1 paths before stage authority, then uses its own campaign, header,
terminal, and exclusive result identities. Its reader binds the journal
envelope campaign to the semantic header and treats before-stage and after-
stage campaign-wall crossings as different terminal seams. The public-path
test transitions from an absence/bootstrap assertion to exact retained-result
rebinding, so a valid outcome does not manufacture another stale test. This is
still orchestration only: the inherited six-stage GPU mechanism is unchanged
and no stage has run at the source boundary.

ADR-0377 supplies the first retained staged observation. The exact append-only
journal contains a header, six ordered observations, and one completed-pass
terminal; the solver-free reader reconstructs all 126 gates and binds the
artifact to the clean ADR-0376 source commit. Every stage releases both memory
pools. The 40-card allocation model requests 10,046,423,704 bytes and observed
pool use stays below it. The independent direct-scan validation path, not the
forward or refresh kernels, dominates the largest host wall. Consequently the
next architecture boundary separates production forward/source-refresh/query-
only/adjoint lifetimes from validation-only reference, direct-scan, and dot-
product lifetimes, then proves a streamed validation seam on bounded games.
No literal 45-card allocation or runtime path exists yet.

ADR-0378 freezes the successor architecture as an explicit lifetime graph.
The forward table and exact compatible outputs are production state. Complete
repeatability references live on the host and are compared through one fixed
64-MiB staging window. The dot check streams bounded products and retains only
a scalar; a full product temporary is not an unnamed allocator detail. After
the forward dot, forward device state dies before one unique adjoint is born,
while the host source baseline supplies the transpose operand. Semantic roles,
not coincident byte counts, determine ownership. This is a future source model,
not yet a target-capable runtime.

ADR-0379 implements the graph as pure source arithmetic. Unique typed rows are
swept over ten phases; the peak is reconstructed from live rows rather than a
parallel total. The 45-card forward, streamed-dot peak, and post-release
adjoint are 10,772,495,644, 11,755,029,796, and 9,645,290,380 bytes. One
9,353,336,216-byte host peak holds complete reference state and a fixed staging
window. The old validation schedule is retained only as a 20,349,274,988-byte
counterfactual, or 21,264,700,268 bytes with its possible full product. The
new source has no device entry; a bounded CUDA seam must prove that real
allocations follow this graph.

ADR-0380 fixes that bounded seam's architecture before source. Its only public
operation runs complete 10- then 22-card populations. A single active-unary
buffer is overwritten for refresh classes; complete source, compatible,
numerator, and reach references live on the host; a 64-MiB staging window
forces the 22-card source through two ordered chunks; and Float64 dot partials
are combined on the host without a full device product. Source and compatible
state must be observably released before the unique adjoint is born. Pool
used/total and physical free memory are evidence at each transition, while 45
cards and every target compiler path remain structurally unreachable.

ADR-0381 implements and validates that architecture. The device owns one
overwritten unary, one forward recurrence, compatible/scalar outputs, and
static topology until the forward dot. Host references and one 64-MiB window
provide literal-byte authority. The 22-card source requires two chunks. After
the dot, the device retains only the query covector and cardinality offsets;
all forward ownership and cached blocks die before the aggregated query,
four-card recurrence, and unique adjoint are born. Seventeen allocator
snapshots prove the phase order and exact final release. This bounded seam is
now reusable validation infrastructure, but target construction remains
absent.

ADR-0382 prospectively wraps the literal form in a clean-process evidence
boundary. A no-argument owner will make its journal durable before target
import, perform typed host/device admission before large allocation, stream
the 8.34-GB source reference in 125 chunks, preserve the same forward-to-
adjoint ownership seam, and retain one permanent pass/rejection/failure
terminal. The owner, target adapter, and artifact do not yet exist; this is an
architecture freeze, not allocator evidence.

ADR-0383 implements that boundary while leaving it uninvoked. The source
layer is deliberately split: a lazy target adapter owns the 45-card numeric
mechanism; an exclusive no-argument runner fsyncs the header before loading
any fallible dependency; and a standard-library reader reconstructs every
terminal from raw admission, allocation, ownership, numerical, chunk, wall,
and release fields. Thirty-five allocation births are typed to their exact
ordinal, predecessor transition, and partial-work state, and the
forward/adjoint seam has only the query
covector plus cardinality offsets live across it. Stored pass labels and
reporting digests have no authority.

ADR-0384 retains the only invocation and closes the owner. The exact
literal-45 geometry runs through all 17 ownership transitions with a maximum
11,620,834,304-byte pool total, then returns default and pinned pools to zero.
The independent reader reconstructs all 27 gates from the 21,663-byte journal.
This makes the occupied-card quotient a viable full-width river contraction
primitive; an actual legal-context adapter into leaf-adjoint evaluation is a
separate architecture boundary, as are resolver rounds and action timing.

ADR-0385 freezes that adapter boundary. Table seats `(1,2,3,0,4,5)` map to
logical contraction axes so the controlled singleton remains query-side;
physical cards outside the board and controlled hand map bijectively to the
45 local quotient cards. The first payoff seam is deliberately one flat,
six-way 60-chip pot: only there does the current fractional showdown automaton
equal the betting kernel's integer odd-chip settlement for every tie count.
Side pots, unequal sunk contributions, and nonintegral tie shares reject.

ADR-0386 implements and source-seals the boundary. The full host fixture is
rank 175/width 176 but produces no quotient value. Warm rebinding reconstructs
the legal provenance and verifies card, hand, topology, terminal, and
automaton identities before replacing unary or mode factors. Ownership is
unit-typed: resident and warm byte views are nonadditive because warm buffers
are resident buffers, while Python card/hand structure is counted in entries
rather than guessed as numeric bytes. Odd-chip and side-pot leaves remain a
separate unresolved architecture problem.

ADR-0387 freezes the proposed consumer schedule before implementation. The
176 global columns are partitioned as `[0,128)` and `[128,176)`; the second
slice alone owns reach feature 175, and both slices contribute partial
numerator/reach before one final normalization. A 128-column physical
workspace is reused, with the 48-column slice recorded as a nonadditive active
view. Forward signs and folds bounded record chunks; adjoint aggregates only
whole six-label occupancies and streams unique source occupancies. Full
compatible, query-covector, unique-adjoint, and record-expanded-adjoint arrays
are architectural rejections. Phase ownership requires complete forward
release before adjoint birth, and the source capacity verdict remains open.

ADR-0388 implements the source schedule without importing CuPy or evaluating a
45-card quotient. The parent bridge's aggregate ledgers expand into 58 unique
physical shape/dtype rows; warm buffers remain nonadditive aliases. A lifetime
sweep places the host peak at 15,973,968 bytes and the device peak at
9,910,940,332 bytes in the first forward source phase. Forward operator/fold
rows are absent before adjoint birth. Fixed numeric and minimum-physical
reserve gates pass, but live allocator admission remains unknown. An
independent direct-mask oracle over the complete ten-card population proves
the global 128+48 forward/fold/adjoint and transpose seam exactly; it does not
stand in for the legal 45-card context or a runtime result.

ADR-0389 freezes the device-consumer seam before implementation. The additive
CUDA module cannot reuse the older zero-based monolithic kernels: source,
signed-target, fold, and covector operations carry an explicit global feature
offset, active width, and 128-column physical stride. Reach is written only by
slice 1; numerator and reach normalize once after both slices. Forward records,
complete six-label query occupancies, and source occupancies retain different
chunk types. The adjoint source contraction is fused over the 90 exact pairing
weights and streamed unique adjoint, so neither source coefficients nor a
record-expanded source adjoint is materialized. Fixed pairwise reductions and
two byte-identical passes replace atomic floating accumulation.

The future owner has 25 named numeric births and phase-exact telemetry from
zero pools through absolute release. The 9,910,940,332-byte prospective peak
must pass contemporaneous free-memory admission, not merely repeat source
arithmetic. Complete ten-card exact and 25-card multi-chunk device controls
precede any actual-context authority. Source sealing leaves the durable actual
result absent; a later one-shot invocation is a distinct boundary.

ADR-0390 rejects that source seal at the bounded numerical boundary. The
offset-aware operator, global online pair tree, normalize-once fold, streamed
unique adjoint, and ownership seam all survive complete controls. The global
tree stores its carry only in dead owned storage—source levels above every
forward target subset and consumed query-covector rows during adjoint—so chunk
cuts cannot change bytes and no allocation is added. A fused adjoint thread
reconstructs one 128-wide local coefficient row in forward pairing order;
compiler-selected local storage is still not a materialized source matrix.

At 25 cards, however, the forward and transpose unnormalized chip-mass totals
round to adjacent Float64 values. Exact summation of their already-rounded
contribution rows preserves that distinction, locating the residual inside
the operator arithmetic rather than the global reducer. The next architecture
hypothesis is paired high/low feature tiling: use the same physical 128 columns
for at most 64 logical compensated features, never a second recurrence table.
That successor requires a new preregistration and must re-prove memory/work,
global offsets, direct rows, chunk identity, and both absolute/relative
conjuncts before any actual owner exists.

ADR-0391 freezes that successor architecture before source. Logical tiles
`[0,64)`, `[64,128)`, and `[128,176)` use interleaved `(high, low)` physical
pairs; the final tile occupies 96 columns and owns reach at physical 94/95.
Source products, both recurrences, signed extraction, fold, adjoint, fused
source contraction, and the global online tree retain the pair. Consumed
compatible and unique-adjoint rows hold scalar low components, so no new full
record array or recurrence table appears. Eight fixed scalar slots store tile
partials by logical ordinal and are reused after the forward/adjoint phase
boundary, raising the modeled peak by only 48 bytes to 9,910,940,380.

The deciding scalar is the exact binary-rational value of both pair components,
not a prematurely collapsed Float64. Complete bounded contribution streams are
also summed independently with `Fraction.from_float`; that audits reduction
but is not mislabeled exact operator ground truth. Original direct-row oracles,
absolute and relative conjuncts, chunk/repeat/tile byte identities, and memory
and wall controls remain independent gates.

ADR-0392 closes two arithmetic holes before implementation. Each zeta-level
pair sum is divided by its exact integer denominator with two residual
corrections, never by an opportunistic reciprocal multiply. Source weights
apply unary then mode factors for seats 0–2; query weights begin at the mixture
and apply unary then mode for seats 3–5. Query covectors remain paired, and
both fold and source-adjoint contraction multiply pairs in increasing global-
feature order. The post-tile chip ratio is formed from exact pair fractions;
no device pair/pair division or collapsed value gains authority.

ADR-0393 retains this implementation but rejects its source seal on wall time.
The pair arithmetic is sound on all opened controls: complete ten-card forward
and adjoint represented values differ by only about `1.45e-25`, and every
opened byte/lifecycle seam passes. The complete 25-card campaign never reaches
a scalar before its frozen wall. Static inspection finds that the new direct
fold oracle repeats combinatorial source unranking once per selected feature,
about 498.7 million source-row visits per three-tile sample before repeat and
alternate execution; this is a plausible cost source, not a measured phase
attribution. The rejected implementation cannot be repaired in place. A
successor first needs phase-separated work authority and a conservative
complete-wall projection, then a distinct numerical invocation.

ADR-0394 freezes that authority without opening an implementation. The direct
query and fold traverse selected query, tile, then increasing source rank;
each source is unranked once and its applicable boundary or logical features
are updated in increasing order. The direct adjoint traverses selected source,
tile, then increasing query record, building one paired query weight per
compatible record before updating ordered boundary features. Coefficients are
still summed by increasing source rank and folded by increasing global feature,
so traversal optimization does not reassociate the pair arithmetic.

The source-sealed preflight partitions each complete 10/22 campaign into 16
contiguous host-wall phases. Raw executed-work counters and synchronized
`perf_counter_ns` spans are deciding; CUDA events are diagnostic. Each
complete-25 phase upper is the worse 10- or 22-card exact-work projection,
multiplied by 5/4 and increased by 1 ms. Their sum must fit 180 seconds before
a later 25-card numerical authority can even be proposed. Population 25 has no
fixture/compiler/device path in this boundary, and a capacity pass would still
say nothing about its numerical seam, resolver latency, or decision quality.

ADR-0395 corrects the compiler-resource seam prospectively: the retained
compiler payload must be an ELF cubin before load, raw CUDA-13.3 `cuobjdump`
resource text and driver function attributes are both retained, and the
standard-library reader reconstructs the per-kernel maxima. The gates are 255
registers and 4,096 stack-plus-local backing bytes per thread; a 131,072-thread
resident upper bound prices at most 536,870,912 backing bytes inside the
inherited 2 GB device reserve. Exact spill traffic is deliberately unavailable.
ADR-0396 source-seals this composite without device execution. Both producer
and reader also enumerate every phase's work, live-shape, and relevant chunk-
count ratios; raw shared host boundaries make gaps, overlaps, and false sums
detectable. The one-shot 10/22 result was absent at that source boundary.

ADR-0397 permanently closes that v1 owner after its first public command. The
durable parent reached clean provenance, but the controller derived its child
module from runtime `__name__`; under `python -m`, this became `__main__`, and
the child failed module resolution before importing the worker or CuPy. The
retained journal therefore has no phase or projection authority. A successor
must use a new lifecycle identity, a literal importable worker module, and a
real no-CUDA subprocess handshake while reusing the unchanged scientific
source by hash.

ADR-0398 freezes that successor architecture before code. Handshake and
campaign modes share one subprocess transport; a fresh challenge and explicit
module/import facts make real worker birth observable without CUDA. The v2
reader first owns the new lifecycle grammar, then passes only the unchanged
scientific event view to the hash-bound v1 scientific rebinder in memory. The
view is never evidence and cannot repair or rewrite either journal.

ADR-0399 implements and source-seals this split. The shared transport has a
bounded cancellable stdout queue, bounded concurrent stderr, exact deadline
after stdout EOF, strict terminal ordering, and explicit pipe cleanup. The
public owner journals the independently known parent challenge digest beside
the child reply before any campaign child can start. Sixteen controls pass;
campaign mode and the real v2 artifact remain unopened.

ADR-0400 shows the transport succeeded but the next typed boundary did not.
The scientific failure reporter's `_plain` fallback recognizes objects via
`__dict__`; `CudaRuntimeIdentity` is a frozen slots dataclass and therefore
rejected. Because this occurred while handling a compiler/resource exception,
the antecedent was masked. Any v3 must add a schema-aware dataclass encoder in
new source, inventory every concrete emitted type, and test the reporter with
the real runtime type through the exact send/framing seam.

ADR-0401 freezes the additive design. The adapter admits the exact runtime
dataclass and its six declared fields only; generic object serialization is
forbidden. In an isolated child it temporarily replaces only the scientific
normalizer, restores the original in `finally`, and proves the real exception
handler with a no-CUDA sentinel compiler failure. V3 handshake, probe, and
campaign share one new transport and evidence identity.

ADR-0402 source-seals the implementation. Type classification precedes generic
container conversion, so an unknown dataclass or named tuple cannot masquerade
as a permitted sequence. The independent reader validates V3 lifecycle and
probe evidence before creating in-memory V2 and V1 validation views. Sixteen
corrected controls pass; the real campaign and result remain unopened.

ADR-0403 closes that real campaign at the next independent boundary. The
serializer and transport retain the actual typed CUDA failure, but the CUDA
13.3 resource-usage subprocess returns status 4294967295. Because the sealed
instrument used `check=True`, its stdout/stderr and temporary cubin do not
survive. A successor must therefore qualify the inspection seam before
capacity work: exact cubin retention, raw nonzero streams, independent parse,
three direct-kernel rows, and conservative driver/cubin maxima are required.

ADR-0404 separates binary capture from semantic selection. A future diagnostic
uses the immutable `_kernels` compile path once, fsyncs a bounded base64 copy
of the exact ELF plus driver rows, then records five ordered `cuobjdump` and
`nvdisasm` command outcomes in binary mode with `check=False`. Its independent
reader rehashes every blob. The output is an offline qualification corpus;
`selected_inspector` and every calibration/resource verdict remain null.

ADR-0405 seals the process boundary. Child progress is ACK-gated by the
parent's post-fsync receipt, so cubin durability and command ordering are
causal rather than inferred from timestamps. The parent keeps stdout/stderr
drains and the wall live through silence and EOF, rejects post-terminal data,
and prospectively prices the exact next journal envelope plus worst-case
terminal before append. Mapping key order is explicitly non-semantic.

ADR-0406 retains the resulting offline-inspection corpus. The CUDA driver
loads the exact 514,039-byte ELF-magic payload and exposes all named kernels,
but CUDA 13.3 `cuobjdump` reports no device code and `nvdisasm` reports invalid
ELF for those same retained bytes. This is an unresolved representation/tool
seam, not a kernel or capacity verdict. External-tool inspectability is now a
separate property from ELF magic and driver loadability. A later semantic
selector must be GPU-free, read only the immutable corpus, demand exact rows
for all three direct kernels, and permit an empty result; driver attributes
remain independent evidence and cannot silently satisfy the dual-instrument
contract.

ADR-0407 fixes the artifact-only selector architecture. Of the five retained
commands, only `cuobjdump_resource_usage` may supply the complete external
resource instrument; tool identities, ELF output, and default `nvdisasm` are
supporting evidence. The selector is standard-library and process-free,
requires exact three-kernel `REG`/`STACK`/`LOCAL` rows, pairs them with driver
register/local quantities by name and unit, and computes componentwise maxima.
Instrument qualification is separate from the 255-register and 4,096-byte
resource verdict. Its output algebra explicitly includes
`no_qualified_inspector`.

ADR-0408 source-seals this boundary. The real entry validates result/reserved
absence, config and committed source hashes, then the complete artifact and
its nested diagnostic identities before selection. Its canonical writer opens
the result exclusively only after assessment construction. Synthetic controls
prove that above-ceiling values do not invalidate a semantically complete
instrument and that incomplete instruments remain unselected even when nearby
driver or register evidence exists. The authoritative result remains absent at
the seal.

ADR-0409 closes the selector with `no_qualified_inspector`; no resource row or
gate exists. A later suffix diagnostic may examine one exact structural
hypothesis only: the retained ELF declares a program-header table one byte
longer than its buffer, while the published CuPy 14.2.0 NVRTC wrapper removes
one terminal byte. Any successor must freeze generic ELF bounds and the sole
zero suffix before operation, then inspect and load the identical repaired
bytes. It may not normalize generally, patch site-packages, or infer that the
hypothesis has already passed.

ADR-0410 makes the suffix hypothesis a closed transform rather than a repair
search. A standard ELF64 parser admits only the exact retained header whose
program table is `len+1`; the candidate is the immutable prefix plus one zero.
The repaired bytes become durable before use, back one temporary file for all
offline commands, and are also the exact in-memory module input. A pass needs
complete cuobjdump resource/ELF operations, all fifteen functions, and exact
equality with the original three driver rows. Resource ceilings remain a later
consumer concern.

ADR-0411 source-seals that shape. The child cannot create a temporary or load
a module until the repaired payload event is fsynced and ACKed; every later
event receives the same barrier. The reader independently reconstructs ELF and
derives the terminal from raw streams. Equal 8 MiB payload and stream limits
are represented by different APIs, so later tuning one cannot silently retune
the other. Imports and controls remain device-free; the real result is absent.

ADR-0412 retains the sole result. One appended zero completes the exact
program-table boundary and makes the same 514,040 bytes acceptable to
cuobjdump, nvdisasm, and the CUDA module loader. All fifteen names resolve and
driver rows are unchanged. The resulting REG/STACK/LOCAL parser is qualified
as an instrument only; resource thresholds, calibration phases, and capacity
projection remain consumers that require their own additive adapter.

ADR-0413 freezes that adapter prospectively and rejects an inspector-only byte
swap. V4 must repair the exact live compiler return before `Module.load`, then
load, retain, and inspect the identical repaired object. A process-local
adapter may replace only the serializer, module-loader, and bounded resource-
inspection seams around one immutable scientific call. Driver/cubin maxima,
payload/stream/journal limits, the 10/22 calibration, the 16-phase partition,
and the arithmetic-only population-25 projection remain separate contracts.
No V4 source or result exists at this boundary.

ADR-0414 repairs one pre-source envelope contradiction. Two commands expose
four 8 MiB streams, whose lossless base64 cannot fit the original 16 MiB V4
journal, and a maximum successful stream cannot fit a one-line science event.
The composite design therefore chunks raw streams under a 64 MiB journal and
applies smaller parser-admission bounds only after every chunk is durable. The
scientific and resource contracts do not change.

ADR-0415 source-seals that composite design. A fresh child repairs the exact
live compiler prefix before loading it, resolves all fifteen functions, and
retains the same repaired bytes for bounded inspection. Indexed ACKs make the
parent's append/flush/fsync completion a prerequisite for every child step.
The standard-library reader reconstructs all raw chunks, the repaired ELF,
the three selected resource rows, and the componentwise driver/cubin maxima
before passing an in-memory scientific-only view to the immutable phase and
projection rebinder. The real V4 result remains absent at the seal.

ADR-0416 retains V4's sole invocation. The executed repaired cubin passes the
resource contract, both complete 10/22 populations pass the paired numerical
and order contracts, and the reader reconstructs all 3,052 phase rows. The
capacity authority nevertheless rejects: the frozen worse-endpoint projection
is 7,260.753615922 seconds against 180 seconds, with no population-25 fixture
or value opened. The consumed V4 architecture cannot be tuned or replayed.
Any successor must prospectively remove or factor exact work in the measured
dominant phases while preserving the operator, canonical accumulation order,
resource pairing, and independent reader.

ADR-0417 freezes the first exact factorization. For a selected query and
logical feature, both direct kernels currently fold the identical compatible
source terms in increasing colex rank. The fold kernel owns all 176 finished
coefficient pairs; the eight query pairs are projections of those slots, not a
second computation. The successor keeps the unchanged query kernel only as a
future differential control and replaces exactly the fold-kernel span so one
thread, one source traversal, and one coefficient vector produce both outputs.
Population execution may not launch the reference query kernel. The source
seal is CPU/static only; device identity, resources, capacity, and action time
remain unopened.

ADR-0418 seals that additive source boundary. The generated CUDA keeps the
parent prefix, suffix, and direct-query kernel bytes unchanged; only the
direct-fold kernel gains a distinct query output and copies its boundary slots
after the full coefficient pass. The CPU sequence oracle, brace-aware source
checker, exact work derivation, and adversarial order/index/alias controls pass
without importing CuPy. Device compilation, host launch integration, output
separation, resource rows, and numerical identity remain obligations of a
fresh preregistered differential owner.

ADR-0419 freezes that owner before implementation. The first compiler payload
is durable evidence before a complete-ELF or narrowly structural one-zero
container path can load it. The exact retained V4 cubin is control-only on
complete 10; complete 10/22 population execution uses generated copies of the
outer runner and forward helper, with exactly one inspected substitution in
each and no parent-module patch. The fused launch has a named argument schema:
feature count is slot 9 and logical width is slot 11. A 15-phase partition
merges direct query and fold, but carries no capacity projection authority.

ADR-0420 source-seals the additive device boundary. The owner ACK-gates raw
compiler chunks before a generic complete-ELF or narrowly bounded one-zero
classifier and loads the exact retained object. The retained V4 query kernel is
reachable only inside the complete-ten differential; generated complete 10/22
population code replaces the helper and collection predicate without parent
module patching and rejects reference-query launches. The reader is standard-
library and independently rebuilds compiler, command, resource, complete-ten,
phase, work, Fraction, and terminal semantics. Host boundaries now synchronize
before stamping, and full population elapsed wall is a separate semantic
quantity from summed contiguous phase time. Eighteen fake-device and synthetic
controls also reject cross-family wall overlap and bind commandless cleanup to
an early failure terminal; the real result, population 25, and every capacity
or action claim remain absent until one separately invoked owner terminal
exists.

ADR-0421 permanently closes that public owner identity before import. The
literal `python -m pontius...` command was not self-contained: repository
Python's path omitted `src` when no ambient `PYTHONPATH` existed, so package
resolution failed before exclusive journal creation or the internal handshake.
The internal parent-to-child harness therefore remains unexercised on device,
and the prospective result remains absent but consumed. Any successor needs a
sealed repository-root launcher and must execute that exact launcher in a
scrubbed, device-free handshake before source seal.

ADR-0422 prospectively makes the repository-root script the sole process-birth
primitive for the V2 parent and children. It derives `src` from its own sealed
path and does not inherit package discovery as authority. A scrubbed public
probe must traverse both launcher levels from outside the repository before
science. V2 changes journal protocol/campaign/header/result identities only;
its standard-library reader validates that envelope and then delegates
unchanged event semantics to the source-sealed V1 reader through a checked in-
memory transduction. The consumed V1 runner and all result paths stay closed.

ADR-0423 repairs that prospective transduction before source. The V1 semantic
reader cannot accept a truthful V2 bootstrap without projecting its module
identity. V2 must therefore validate fresh lifecycle provenance itself, then
project only journal protocol/campaign, header identity, wrapper config hash,
and bootstrap literal/spec names. Challenge, runtime, CuPy, every later event,
and the outer terminal are invariant across the seam.

ADR-0424 corrects the V2 parent provenance before source seal. Three ADR-0420
metadata hashes came from a shell expression that rewrote literal escape text,
not line endings. The committed V1 bytes stay fixed; V2 binds the independently
reproduced hashes. Canonical-LF authority must now agree between the production
helper and a byte-by-byte CRLF normalizer that never spells escaped source
tokens.

ADR-0425 source-seals the fresh launch and evidence boundary. A standard-library
root script derives and installs the exact repository `src`, then becomes the
only entry for the public parent, no-CUDA handshake child, and campaign child.
The V2 reader first validates the fresh protocol, campaign, header, dependency,
wrapper, and unique-bootstrap lifecycle. It then projects only ten literal
lifecycle paths into an in-memory V1 envelope; every post-bootstrap science
event and the outer terminal remain unchanged for the owner-free V1 semantic
reader. The scrubbed two-launcher probe and 38 combined controls pass without a
CuPy import, device operation, or result. This is launch/evidence readiness,
not a device, capacity, action-clock, or quality result.

ADR-0426 consumes the sole V2 launch. The process tree and pre-population device
boundary pass, and both population-10 families release, but the generated
runner resolved `_sample_rows` from the older paired module while evidence used
ADR-0394 `sample_rows`. Their compatible callable signatures hid different
populations: seven execution rows versus sixteen authority rows. The first
source comparison rejects 56 actual pairs against 128 expected pairs before a
population object exists. A successor must compile one immutable sample-plan
object and inject its identity into execution and evidence; helper selection,
rank arrays, and comparison shapes become pre-device invariants.

ADR-0427 freezes that V3 seam prospectively. `CalibrationSamplePlan` is one
frozen object per population in a read-only mapping, containing the literal
source ranks, labeled query records, boundary features, and expected source/
query/fold/adjoint pair shapes. The generated runner's global resolver and the
evidence calculator must consume those exact objects. Source controls inspect
the compiled function globals and force the historical 7/16 helper, rank,
feature, and shape mutations to reject before any CuPy import. V3 otherwise
inherits the V2 device science and lifecycle through fresh identities.

ADR-0428 source-seals the implementation. The read-only resolver is injected
into the generated population function and exact evidence calculator, while
explicit identity gates also bind the population-evidence wrapper, family
runner, and top-level validation function. Every normal and direct sample shape
is checked before Fraction evidence. The fresh reader independently validates
V3 lifecycle, then changes only the frozen header/wrapper/bootstrap identity
paths in memory for the owner-free V2 semantic oracle; post-bootstrap science
and the outer terminal are byte-semantically unchanged. No CuPy or result work
occurs during the seal. One later clean V3 invocation is the only open authority.

ADR-0429 consumes that authority and retains a passing complete 10/22 device
validation. The same immutable plan reaches generated execution and evidence,
both population rows survive all exact numerical/work/lifecycle checks, and the
independent nested reader accepts the complete journal. The 49.419-second
population-22 value is the whole validation population wall, not a resolver
iteration or action response. V3 contains no capacity projection and cannot be
scaled to population 25 by inference; the next boundary is a separately frozen,
artifact-only fit assessor.

ADR-0430 freezes the assessor architecture before source. A device-free reader
rehydrates the immutable V3 journal, extracts exact population phase/work rows,
and prices fifteen device phases with frozen 25/10 and 25/22 constituent ratios.
The fused shared phase uses the complete fold-plus-copy work envelope. A
sixteenth `population_envelope_outside_phase_partition` component prices the
nonnegative difference between complete population wall and contiguous phase
sum at fixed evidence scope. Maximum endpoint, 5/4 guard, 1 ms component guard,
and 180-second limit remain integer-only and independently rederived.

ADR-0431 source-seals the implementation while keeping the deterministic real
projection unopened. The assessor's import boundary is file/process/device
free; its explicit artifact path first invokes the complete V3 semantic reader
and then independently reconstructs raw phase partitions, exact work, phase
sums, population walls, and outside envelopes. Fourteen ratios reproduce the
parent constituent algebra; the fused ratio is the maximum of five named work
constituents, including fixed boundary copies. The result reader shares no
assessor or owner code and independently derives the canonical result and
terminal. The owner requires clean tracked dependencies and writes once with
`xb`, flush, and fsync. Population 25 remains integer geometry only.

ADR-0432 consumes the owner and retains a `completed_capacity_rejection`.
Every component's maximum comes from population 10; the 4,999.487-second sum is
27.775 times the 180-second validation wall. The fused phase supplies 51.5622%
and is independently fatal, but the remaining rows still total 2,421.641
seconds. The 168.156-second 22-only projection stays reporting-only. This
closes the paired/shared representation under the frozen estimator, not all
exact representations. An exact-integer successor must begin with complete
CPU algebra, signed carry/rounding bounds, and source-only work/memory pricing.

ADR-0433 freezes that successor's first boundary. The integer authority begins
at exact dyadic values of captured high/low rows, covectors, and weights; it
does not retroactively make pair capture exact to original factors. A global
720 scale removes internal division, with six-card forward weights
`{1,6,30,120,360}` and four-card adjoint weights
`{30,120,360,720,720}`. Their resulting bilinear integers must match exactly.
Family-wide fixed-point exponents, signed partial and scalar bounds, one guard
limb, and integer-only ties-to-even terminal rounding are explicit. The old
ten-card exponent envelope implies five guard-inclusive table limbs but nine
for scalar accumulators; every future fixed-limb config still needs its own
prospectively frozen per-run exponent admission. Literal-45 rank, recurrence,
memory-liveness, fixed-side, and sparse-delta counts remain symbolic CPU work,
not a device-fit, latency, population-25, or quality result.

ADR-0434 corrects only the parent-provenance layer before that source can
seal. Three ADR-0433 hashes were produced by replacing the four literal bytes
backslash-r-backslash-n inside source text. The parents are unchanged. Future
binding loads both configs, hashes actual bytes with CRLF-only normalization,
and requires an independent byte-loop implementation to agree for every
parent. The literal-token rewrite survives only as a mutation that must
reproduce and reject the historical false values. No operator, bound,
rounding, population, work, memory, delta, device, or claims contract changes.

ADR-0435 source-seals that CPU operator. Its complete input carries explicit
query-label identity as well as masks: every four-card occupancy must contain
labels `{0,1,2,3,4,5}` exactly once before aggregation. This prevents a count
of six duplicate records from standing in for semantic coverage. The natural
complete-ten captured-pair population and signed complete-twelve population
match independent literal Fraction authorities; direct factorial induction,
fixed-width emulation, exact rounding, and delta/cold identity controls pass.
The sealed module remains an unbounded-integer authority only. Positional
limbs, residue channels, selective adjoint queries, child-rank traversal, and
device execution remain separate prospective mechanisms.

ADR-0436 prospectively types those mechanisms before source. A selective
forward or adjoint query reads 16 or 57 transformed subset rows; exact global
certificate closure still covers every legal omission, but may stream rather
than retain the dense output. Signed positional limbs and a fixed RRNS code
share one unbounded-integer authority. RRNS uses eight ascending working primes
and one larger redundant prime, exact `M >= 2B+1` admission, full-CRT range and
working-CRT/base-extension checks, and claims detection only when one channel's
final checked residue changes. It neither corrects nor detects a correlated
all-channel logic error. Row-owned colex child ranking, resident table options,
canonical per-family exponent admission, reporting-only `frexp`, and separate
primitive work counters remain CPU source-seal subjects; device compilation,
fit, speed, population 25, and actual 45-card values remain closed.

ADR-0437 makes the comparison's self-seal provenance control nonvacuous. The
forbidden literal-token rewrite is evaluated over every bound file, but only a
file whose frozen raw occurrence count is positive is rejecting-mutation
evidence. Existing token-free parents retain identity digests; five existing
parents retain exact positive counts and changed mutation digests. The new
comparison source and controls must each contain exactly one occurrence, then
change bytes and digest under the forbidden rewrite. Production CRLF
replacement and the independent state-machine byte loop must agree on
normalized bytes while sharing no helper or replacement implementation.

ADR-0438 implements and source-seals the CPU comparison. Fixed-point family
encoding and labeled-query aggregation now occur inside each candidate path;
positional limbs and both RRNS schedules then reproduce ADR-0435's recurrences,
rows, scalars, reach, and terminal bits on complete 10 and signed 12. RRNS
reconstruction remains fail-closed under only the frozen one-changed-channel
model. Selective 16/57-row evaluators and an iterable complete-domain scanner
are separate interfaces; the latter retains neither output rows nor a price
map. Literal-45 work and memory remain formulas, with batched channel traffic,
replay, and forward/adjoint scratch stated separately. Neither representation
is selected before compiled resource and bounded-wall evidence.

ADR-0439 prospectively freezes that compiled evidence boundary. All schedule
arms share one literal CUDA 13.3 NVCC translation unit and direct `sm_120`
cubin. Raw compiler logs and cubin bytes become durable before parsing; the
same bytes reach ptxas-log interpretation, cuobjdump, nvdisasm, and the module
loader. Ptxas spill bytes, cubin/driver stack-local backing, and static local
instruction sites are separate types, with conservative cross-instrument
maxima for registers and backing and no fallback for missing fields.

Device-memory admission is an exact lifetime sweep over named buffers, not a
sum of mutually exclusive workspaces. Forward and adjoint tables cannot
coexist, and the batched RRNS table can be overwritten only after its first-
batch output is drained; its second recurrence traffic remains fully charged.
Only complete 10 and signed 12 may execute. Consecutive synchronized host
boundaries partition every candidate and the whole laboratory exactly; device
events are reporting only. This preflight can make an arm eligible but cannot
select it or establish population-25, actual-45, resolver, 15-second, action,
quality, truncation, blueprint, or strength behavior.

ADR-0440 repairs the phase topology before source seal. A single-pass arm has
one twelve-interval partition. Batched-five-then-four RRNS cannot honestly use
that same topology while also draining its first outputs, reusing one table
workspace, and replaying the recurrence. It therefore has one ordered twenty-
interval partition: channels `0,1,2,3,8`, drain/reuse, then channels
`4,5,6,7`, followed by scalar transfer/reconstruction, verification transfer/
differential, and cleanup. No interval is reentered or merged across a gap.
The source-side memory contract also keeps source level six as captured
high/low pairs; fixed-width forward storage begins only at level five. This is
the ADR-0438 hybrid made explicit, not a timing-conditioned optimization.

ADR-0441 source-seals that corrected experiment without importing CuPy or
touching a compiler, device, or result. One repository-root launcher reaches
an exclusive append/fsync/ACK owner; one literal translation unit contains all
sixteen kernels; and one standard-library reader reconstructs provenance,
resource maxima, symbolic buffer liveness, execution schedules, phase walls,
and eligibility. Each population's host-authority digest/scalar manifest is
durable before its candidate evidence. RRNS candidate records carry original
table and scalar codewords, so the reader independently replays every frozen
single-channel mutation and the correlated all-channel boundary rather than
accepting stored verification booleans. The seal authorizes one reduced-device
preflight invocation only; it establishes no candidate winner, actual-45 fit,
15-second action latency, or decision quality.

ADR-0442 consumes that invocation at the host-compiler boundary. The root
launcher and durable owner reached the bound CUDA 13.3 tools, but NVCC could
not find `cl.exe`; no cubin, resource inspection, device query, module, or
kernel exists. This exposes the host compiler and activated INCLUDE/LIB/PATH
environment as part of compiled-tool identity, not ambient workstation setup.
Any successor therefore needs a fresh owner/result identity and a no-compile
source-seal handshake that resolves one explicitly bound supported x64 MSVC
toolchain from a scrubbed environment. Installing that external toolchain is
not a repository mutation and requires explicit user authorization.

ADR-0443 freezes the authorized prerequisite and the additive recovery shape.
The successor reconstructs `vcvars64` from a small scrubbed baseline and
requires exact full and selected environment digests, x64 host/target, MSVC
14.44, Windows SDK 10.0.26100.0, and hash-bound compiler/linker/resource tools.
The activated environment replaces ambient process state; an absolute bound
Git executable preserves clean-source checks. Activation starts inside the
public clock but outside the unchanged scientific laboratory. A fresh wrapper
may parameterize only owner identity/lifecycle fields around the byte-identical
ADR-0441 scientific module; its standard-library reader independently validates
that allowlist and may not project scientific observations or terminals.

ADR-0444 source-seals the implementation. The environment wrapper double-hashes
bound host files around activation, replaces ambient state, and injects the
pre-activation public origin into the inherited durable owner. Owner globals
are scoped and restored. The reader verifies the untouched v2 chain and host
header before rebuilding a private chain with exactly one header module-name
projection; its parent-reader bindings are lock-scoped and restored. Synthetic
controls prove the scientific observations and terminals are preserved and the
retained v1 result remains independently readable. This opens one v2 invocation
only, not a candidate or production consumer.

ADR-0445 consumes that invocation at a distinct environment seam. The scrubbed
`vcvars64` mapping is the parent compiler environment, while package
initialization deterministically prepends the repository CUDA-wheel DLL
directory to the campaign child's `PATH`; those mappings are no longer one
identity by numerical coincidence. The retained two-record journal terminates
before bootstrap with zero events. Because the source-sealed v2 reader wrongly
required an observation, a separate artifact-bound assessor validates the
exact raw result, durable chain, historical Git-blob dependencies, header, and
zero-event terminal without editing either consumed v2 module. A successor
must bind parent and child environments separately and make zero-event terminal
handling part of the reader contract.

ADR-0446 freezes that split before successor source. The parent remains the
exact 55-key compiler mapping. The child has its own 55-key activated
projection and exact 63-key complete domain: one CUDA-wheel prefix changes
`PATH`, six static Python/CUDA bootstrap variables are fixed, campaign mode is
fixed, and only the resolved spool path is dynamic. Five repository-required
DLLs are size/hash-bound, the prefix occurs once, and the same host compiler
tools must resolve behind it. The fresh reader has two explicit lifecycle
branches: fully validate zero-event infrastructure terminals, or require
bootstrap first and reuse the unchanged scientific reader after a measured
header-only projection.

ADR-0447 source-seals the implementation without compiler or device work. The
fresh runner validates the exact complete child domain inside the actual child
process before entering the inherited campaign, while the parent records the
same independently derived runtime evidence in the durable header. The reader
has a first-class zero-event branch and otherwise performs a two-field header
projection before the existing v2-to-v1 semantic chain. All projected globals,
including the fresh preregistration commit, are lock-scoped and restored. One
clean v3 invocation is now eligible; no arm or production consumer is selected.

ADR-0448 consumes that identity with a passing compiled-device preflight. One
CUDA 13.3 cubin executes all three fixed-width schedules exactly on complete-10
and signed-12, with no recorded spill loads or stores. Positional and batched-
five-then-four RRNS pass the frozen resource, wall, exactness, fault-contract,
and symbolic literal-45 memory conjuncts; resident-nine RRNS fails only because
its symbolic 16.414 GB peak exceeds available memory after reserve by 1.319 GB.
The retained reduced-population walls cross by population, so no post-outcome
aggregation elects a winner. The artifact-bound assessor preserves the exact
journal and historical source blobs. A prospective actual-45 fit boundary must
carry both eligible arms and distinguish symbolic fit, live allocation,
operator work, resolver iteration, and the authoritative 15-second action
clock.

ADR-0449 freezes the first part of that boundary as a GPU-free artifact-only
admission screen. It projects every retained timed phase of positional and
batched RRNS independently from both reduced endpoints to exact literal-45
integer work constituents, takes the largest constituent ratio and endpoint,
then applies a `5/4` plus 1 ms per-phase guard. The arm-local sum is compared
with 14 seconds, preserving the action clock's one-second emission reserve.
This is a conservative policy for deciding whether a live attempt is worth
running, not measured literal-45 latency or action fit. The retained symbolic
memory peaks remain required but are not live allocations, and actual input
exponent windows remain a separate prerequisite before any target arithmetic.

ADR-0450 corrects the accounting before projector source. The independent
exact-differential transfer remains mandatory laboratory validation but is not
production work and therefore cannot enter the 14-second component sum. Every
runtime certificate, fault, global-scan, reconstruction, and cleanup phase
stays charged; the runtime and laboratory phase sets must form an exact ordered
partition. The prospective result also moves to the existing
`artifacts/work_preflight/*.jsonl -text` domain, and a no-argument root launcher
is frozen before implementation.

ADR-0451 source-seals that corrected projector without reading the retained
parent journal or creating its result. The standard-library projector retains
all six timed observations, independently prices both calibration endpoints by
the maximum exact constituent ratio, and reports endpoint-only counterfactuals
without letting them decide. Runtime and validation totals remain separate.
The independent reader does not import the projector: it rebuilds the raw
parent schedule, integer geometry, ratios, ceilings, guards, memory conjuncts,
survivors, and terminal, then verifies every dependency against the clean
historical source commit. One exclusive artifact-only invocation is now
eligible; no live literal-45 device work or candidate selection is.

ADR-0452 retains the sole projection as a complete rejection. Positional
projects to 3,186.554546230 seconds and batched RRNS to 9,908.352862122 seconds
against the 14-second component allowance; both still pass symbolic memory,
and neither is selected. The complete adjoint global scan accounts for 90.69%
of positional runtime, while the two batched adjoint scans account for 92.77%.
These are conservative projections, not measured target latency. A successor
may use selector-local queries during warm exploration, but final authority
must still close every omitted row through exact global separation or a
conservative bound. Active-basis exactness cannot stand in for global closure.

## Runtime target

The final agent will always have an immediate blueprint fallback. CPU code will
construct and mutate trees. Stable tree epochs and neural leaf batches may run
on the GPU. Current-decision jobs preempt speculative future work. No cached
strategy is reused without validating its public state, belief representation,
blueprint version, and exact joint-range provenance. Structurally similar range
entries are warm-start candidates, not strategy hits.

## Dependency direction

Game definitions do not depend on solvers. Exact evaluation and solvers depend
only on the generic game interface. Models and optimized runtimes must not
become required dependencies for correctness tests.
