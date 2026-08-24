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
