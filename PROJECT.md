# Project Charter

## Objective

Build and measure a six-player no-limit Texas hold'em research agent that uses
an offline blueprint, public-belief search, neural continuation values, adaptive
actions and trees, and deadline-aware allocation of computation. The primary
deployment objective is maximum marginal chip-valued decision quality per
additional millisecond of attributable online workstation compute, subject to
one hard 15,000 ms wall-clock response deadline whenever the controlled seat
acts on a Ryzen 9 9900X, 64 GB host-memory, RTX 5080 workstation.

## Game contract

- Six-player cash-game no-limit Texas hold'em.
- 100 big-blind starting stacks.
- No rake and no ante in the first full-game implementation.
- Exact legal betting, all-in, side-pot, and card-removal rules.
- Each controlled action has one continuous 15,000 ms wall-clock response
  deadline, including a fixed 1,000 ms synchronization and emission reserve.
  It starts when an observed event makes the controlled seat the actor and
  includes every pause and work interval through emission. A later controlled
  action receives a new response wall.
- Opponent think and transport idle before that clock starts do not consume the
  response wall. Agent work during that opportunity, including prior-street and
  opponent-turn speculation, is online preparation rather than free time. It
  may benefit a decision only through an exact provenance-bound artifact hit.
  Report all preparation spent, credited, missed, invalidated, and aborted
  separately; concurrent CPU/GPU work is elapsed wall time rather than summed
  device time.
- Pontius banks computed artifacts, not unused milliseconds. Preparation never
  extends the live 15-second response deadline unless a future host exposes a
  separate rules-defined time bank. Offline training cost remains separate.
- Cold-cache and warm-cache results are reported separately.

## Current decision-boundary contract

- The active systems control is a prepared six-player h32 river decision.
- The additive exact-game control is ADR-0290's complete explicit-deal
  reference loop. It joins ADR-0286's six-seat integer-chip legal decision
  spine to future-blind one-seat cards, five complete opponent axes with hard
  card disjointness, exact rational public-action updates, a digest-bound
  deliberately weak policy and fallback, showdown, and settlement. It does not
  compute normalized full-width marginals and is not a calibrated range,
  trained full-game blueprint, action abstraction, or strategy-producing
  resolver.
- ADR-0292 rejects the first fixed pot-fraction action lattice at its frozen
  reduced sizing-quality gate before complete-hand integration. Its exact
  legality/projector code is a parked control, not the action abstraction of
  the reference loop. A successor must use a preregistered
  development/confirmation split and may not tune to the opened failure.
- ADR-0294 also rejects the dyadic successor before replay integration because
  its untouched panel contains only five informative contexts rather than
  eight. Favorable conditional loss and recovery diagnostics do not waive that
  power gate. Candidate-blind evaluation-power design must precede v3.
- ADR-0296 rejects the first candidate-blind pool qualifier when its second
  replication yields 11 rather than 12 material contexts. Its owned runner now
  makes batch identity and stop-after-target state semantic evidence. Batch 2
  values remain unopened; a richer reduced game must precede v3.
- ADR-0297 preregisters the smallest richer game: four private types per seat
  with the same one-bet tree and candidate-blind controls. Pool construction is
  separated from values. ADR-0298 seals all three structural pools and exact LP
  dimensions. ADR-0299 passes all three replicated width-four yield/work gates
  and authorizes one v3 preregistration on fresh dual panels, not integration.
- ADR-0300 preregisters collision-repair v3 before source code: preserve v2's
  distinct two-pot action and use three-halves pot only when two-pot wastes its
  slot on a mandatory anchor. ADR-0301 now freezes the exhaustively validated
  source digest and two exact fresh seeds. ADR-0302 seals the resulting
  value-free 48-context representative family and separate 96-context
  qualification pool with zero counterpart among 604 maintained prior
  contexts. ADR-0303's candidate-blind runner reaches 24 qualifiers after a
  contiguous 60-context prefix and seals the final qualified panel. ADR-0304
  rejects v3 at the frozen qualified aggregate-recovery gate: both families
  pass maximum and mean normalized-loss limits, but the qualified family
  recovers only 80.05% of the available raw-chip sizing gain versus the 90%
  floor. ADR-0305 prospectively freezes capacity-filling pot-odds v4: retain
  every v3 action under the same seven-raise ceiling, then fill every unused
  slot by exact-rational farthest-point coverage rather than another fitted
  fraction. ADR-0306 now freezes its exhaustively validated, bounded-work
  source at SHA-256
  `37824e44b7793b10b081957fc8be387bdca5c565b4bfe2386ca13f7e1c785c8b`.
  ADR-0309 now seals its 48-context representative and separate 96-context
  qualified-A and qualified-B structures before every value. They are mutually
  unique and have no counterpart in the finite 748-context ADR-0291--0304
  inventory. ADR-0310 rejects the ordered qualification before candidate
  evaluation: A reaches 24 qualifiers after 73 contexts and passes its teacher
  controls, but B's full-integer LP at context 21 fails native primal
  verification. A is provisional, no final A/B panels exist, and every
  representative and candidate value remains unopened. V1-v4 are parked and
  no action abstraction is integrated. The next eligible work is a separately
  preregistered candidate-independent native-simplex robustness audit, not a
  v4 retry. ADR-0311 now freezes that audit before corpus or compiler source:
  one known regression, 48 exact micro LPs, 128 fresh candidate-free sizing
  LPs, five exact representations, and native/HiGHS-DS/HiGHS-IPM arms with
  unit-specific independent bounds. ADR-0312 now seals the pure compiler, 48
  micro inputs, 64 fresh contexts, 177 bases, and 885 exact representations.
  The fresh contexts have zero counterpart in the finite 988-context inventory
  through ADR-0310. ADR-0313 now seals the runner and result-schema source at SHA-256
  `cfb127960e3d501a156f14d22244ecd122874b74fefb668685f9a721503ade16`
  with exact micro enumeration, original-coordinate primal/dual mapping,
  feasible behavioral sizing reconstruction, outward certificates, complete
  failure observations, frozen runtime/options, and the 2,655-call schedule.
  ADR-0313's one-shot complete audit invocation is now retained by ADR-0314:
  all 2,655 arms completed, all 885 HiGHS dual-simplex and all 885 IPM arms
  passed, and native recorded 36 failures. The literal conjunction still
  rejects because its known-regression predicate confused unique maximum row
  215 with the complete above-allowance row set. HiGHS remains ineligible.
  ADR-0315 source-sealed the separate artifact-only correction and synthetic
  multi-row/unique-maximum controls before retained-evidence access. ADR-0316's
  temporally separated exact-digest reanalysis now passes with zero failures
  and makes HiGHS dual simplex eligible only for a later prospective adapter
  evaluation. No adapter, runtime latency, quality result, specialized solver,
  consumer migration, or v4 revival is authorized.
- ADR-0317 separates the compact reduced-sizing LP from the one-seat behavioral
  master. The former still invokes rejected native simplex and is next eligible
  only for a prospectively source-sealed, semantically certified HiGHS
  dual-simplex adapter. The latter already uses HiGHS and accounts for only
  0.063%-0.151% of complete measured time in the two retained six-target
  ledgers; persistent or specialized master work remains parked until a fresh
  certified v2 ledger crosses a 5% perfect-solver materiality trigger. This is
  a scheduling boundary, not an adapter, speedup, or candidate result.
- ADR-0318 implements and canonical-LF source-seals the reduced-sizing
  HiGHS-DS adapter behind exact normalized behavioral reconstruction and an
  outward-rounded trusted-box certificate. Its 11 controls are analytic or
  bounded toys only. A failure-complete, source-sealed 177-canonical-base
  runner must be committed before any retained adapter result; no v1 consumer,
  v1-v4 candidate owner, or action value is connected.
- ADR-0319 source-seals that failure-complete runner, exact canonical schedule,
  one-public-call counter, typed observations, and correctness-only gate before
  any retained invocation. The 48 micro bases use exact enumeration plus an
  outward certificate; the 129 sizing bases pass through ADR-0318 and then the
  separately sealed ADR-0313 reconstruction. Nine unsealed controls pass. No
  canonical result or certified-v2 consumer exists yet.
- ADR-0320 retains the one sealed campaign: 177/177 canonical observations,
  48/48 exact micro gates, and 129/129 sizing adapter plus independent-verifier
  gates pass with one public call each and no clips or failures. The maximum
  sizing interval is `8.50e-11` chips. This finite h4/compact result opens only
  a separately preregistered additive certified-v2 reduced-sizing consumer;
  it is not an action-width, complete-decision latency, or strength result.
- ADR-0321 now prospectively freezes that consumer as a research-only boundary
  before source or fresh values. It accepts only an exact two-live-seat river
  opening shell with a fold/call-only responder, binds a caller-supplied
  kernel-legal raise-to subset and its distinct reduced bet increments, and
  returns certified evidence or a typed no-action rejection to the caller-owned
  legal fallback. It cannot emit a production action or model responder raises.
- ADR-0322 implements and source-seals that exact boundary. Eleven unsealed
  analytic/differential/corruption controls pass; unsupported semantics and
  source/runtime drift make zero backend calls, while accepted or corrupted
  solver attempts make exactly one. Accepted evidence rebinds its immutable
  request and LP; every rejection retains its cause chain and owns no action.
  No fresh action-width value, production integration, or latency claim opens.
- ADR-0323 preregisters a fresh certified finite-block action-width research
  line rather than a fifth fixed ladder. It derives complete integer universes
  from the exact kernel, separates certified full-minus-subset chip intervals
  and exhaustive best-subset teachers from a direct greedy proposer, requires
  exact opponent-row identity and fold/call closure before a finite-block
  price, and reserves commit-derived fresh transfer after mechanism freeze.
  No source, structure, value, action-width result, or live policy exists yet.
- ADR-0324 implements and source-seals only that line's value-free development
  structures: 96 unique h4 contexts, complete exact-kernel integer universes of
  7/9/11 raises, and 12,556 anchored subsets across raise widths two through
  six. Private width, raise width, check, raise-to totals, and payoff span stay
  semantically distinct. No solver call or transfer construction exists; a
  separately source-sealed candidate-blind qualifier is next.
- ADR-0325 source-seals that qualifier and its 192-task full-then-width-two
  schedule before a development value. Certified regret subtracts endpoints as
  `[L_full-U_subset, U_full-L_subset]`; normalized opportunity, chip reversal,
  and chip ambiguity remain separate types. Every stop and unexpected failure
  retains its exact prefix and call-accounting status.
- ADR-0326 retains that one sealed invocation: the exact prefix ends at context
  50 with 16 qualifiers, 35 nonqualifiers, zero ambiguity, and 102 accepted
  one-call arms. A canonical artifact independently rebinds every endpoint and
  request/legal/LP identity without a solver call, and seals the exact
  16-context development panel. All width-three-through-six values remain
  unopened; a source-sealed 2,495-task exhaustive teacher owner is next.
- ADR-0327 source-seals that teacher owner without opening a development
  intermediate-width value. Its exact schedule has 16 full and 2,479 anchored-
  subset tasks; every subset retains conservative chip and payoff-span-
  normalized regret. Teacher maxima are interval envelopes, all certified
  nondominated subsets survive, uniqueness requires one survivor, and the
  reporting-only equivalence set may be empty. Its cardinality is the flatness
  measurement. A no-clobber canonical artifact staging path is reserved before
  any future consumer call, so an incomplete attempt blocks silent retry. One
  retained invocation is next; greedy pricing and transfer remain closed.
- ADR-0328 retains that sole invocation as a complete 2,495-call result and
  commits its exact 4,975,258-byte artifact. A solver-free owner rederives all
  task, request/public/legal/LP, endpoint, regret, normalization, set-valued
  envelope, and nested-digest evidence. Width three is the first exhaustive
  teacher to pass the frozen full-regret maximum and mean limits; it is not a
  selected action width because greedy recovery and width-matched excess are
  unopened. Across widths three through six, 49 of 64 context-widths are
  plateaus, with survivor median 8 and maximum 56. The next gate is source-only
  direct closed finite-block greedy ownership; transfer remains closed.
- ADR-0329 source-seals that complete adaptive owner without opening a price.
  It enumerates 2,479 exact subset arms and all 7,848 possible parent-plus-one-
  raise transitions before values; any realized width-two-through-six path is
  exactly 400 calls. Incumbent, augmented, and own-block response identities
  are semantic fold/call memberships rather than LP row counts. Selection uses
  the greatest behavioral lower endpoint and exact smaller-raise tie break;
  full regret, aggregate recovery, and width-matched teacher excess retain all
  five frozen conjuncts. One no-clobber retained invocation is next; no greedy
  value, selected width, transfer population, capacity result, or action exists.
- ADR-0330 records the single invocation as an unretained artifact failure.
  The completed-result path proves the exact 400-call rule was reached, but a
  width-gate digest included itself and recursed before canonical publication.
  The final artifact is absent; the exact 58-byte `.partial` contains no values
  or selection. The serializer now separates digest-core and artifact-envelope
  payloads, exact witness checks pass, and both public invocation entries are
  permanently closed. A replay cannot recover the result. Any successor must
  use a new commit-derived untouched population and source-seal synthetic
  success serialization plus a write-ahead evidence journal before values.
- ADR-0331 prospectively freezes that non-replay recovery. The exact population
  seed derives from commit `49044e5`; 96 new h4 contexts must be semantically
  disjoint from the complete original 96-context pool. The first source gate is
  value-free and must prove a canonical header + 400 observations + terminal
  journal, self-free hash chaining, append/flush/`fsync` ordering, exact prefix
  recovery, and byte-preserving torn-tail rejection. No new context, value,
  panel, width, transfer seed, or action exists yet.
- ADR-0332 passes that value-free gate. The commit-derived compiler accepts 96
  unique contexts after 551 attempts and proves zero semantic overlap with all
  96 original contexts; its frozen anchored-subset ledger contains 12,352
  subsets. The general journal permits only exclusive construction, returns a
  receipt after write/flush/`fsync`, and preserves exact verified prefixes plus
  untouched tails. A 610,098-byte systems fixture traverses one header, 400
  observations, four populated width summaries with five distinct gates, and
  one terminal; all 402 crash prefixes and representative torn lines pass.
  Every fixture value, including its synthetic width three, is fake. The next
  gate is source-only replacement qualification; no sizing value or panel is
  open.
- ADR-0333 passes that source-only qualification gate. The exact new-pool
  schedule contains 192 complete-universe-then-anchored-width-two tasks and
  the public owner has one consumer call site, no-clobber creation, exact
  receipt-gated continuation, exact rejection contracts, and distinct target,
  exhaustion, ambiguity, nested-reversal, rejection, and unexpected stops.
  Accepted evidence carries exact policy plus raw dual hints; the solver-free
  rebinder reconstructs both interval endpoints and the terminal reduction.
  Synthetic target/failure controls, all complete prefixes, torn tails,
  rehashed semantic corruption, and append failures pass.
- ADR-0334 retains the first and only replacement qualification invocation.
  Its 100-record, 391,986-byte journal contains 98 accepted one-call arms over
  contexts 0 through 48 and an exact target terminal: 16 qualifiers, 33
  nonqualifiers, zero ambiguity, and complete invocation accounting. The
  solver-free result owner rebinds policy and dual witnesses, every
  classification, the terminal, and an exact target-only panel while all
  value-producing paths are tripwired. The panel spans all four pots, all three
  effective stacks, and legal raise counts 7/9/11, but remains an
  opportunity-conditioned h4 heads-up fold/call result. The next checkpoint is
  source-only ownership of its exact 2,113-task exhaustive teacher; no teacher
  value, selected width, transfer, latency, or production action is open.
- ADR-0335 passes that source-only teacher boundary. The exact new-panel
  schedule contains 16 complete-universe arms and 2,097 anchored subsets at
  raise widths two through six. Accepted real evidence must carry an exact
  policy and dual hint; the solver-free reader reconstructs both endpoints,
  conservative regrets, interval-max envelopes, every nondominated survivor,
  sole-survivor uniqueness, and potentially empty reporting equivalence. The
  next arm is authorized only by the preceding post-`fsync` receipt. A complete
  2,115-record synthetic journal rebinds without a consumer or solver call.
  Every replacement teacher value remains unopened; exactly one no-clobber
  retained invocation from a clean source commit is next.
- ADR-0336 retains that sole invocation as an exact 8,027,171-byte,
  2,115-record journal with 2,113 accepted calls and a completed terminal. Its
  solver-free result owner separates the inherited maximum-plus-mean gate, the
  descriptive median knee, and the first all-context zero-lower boundary.
  Width three is first for the gate and median; width four is first with no
  certified-positive lower-regret context because positions 9 and 11 form the
  tail. No direct mechanism or production width is selected. The next boundary
  is source-only ownership of ADR-0331's exact 376-call non-replay direct
  mechanism.
- ADR-0337 passes that source-only direct-mechanism boundary without opening a
  price or value. It seals 2,097 anchored arms, all 6,543 response-closed
  parent-plus-one transitions, and the exact adaptive ledger of 16 initial
  plus 360 candidate calls. Lower behavioral endpoints select, exact ties take
  the smaller raise-to total, chip endpoints are summed before aggregate-
  recovery division, and all five nominal gates are independently recomputed.
  Only the prior post-`fsync` receipt authorizes another call. A complete
  1,227,894-byte, 378-record synthetic journal proves the success serializer,
  dynamic-branch rebinder, smaller-raise tie path, and terminal reduction with
  every consumer and solver path unopened. The next boundary is exactly one
  no-clobber invocation from this clean committed source; no transfer,
  capacity, latency, action, or production-width evidence is eligible first.
- ADR-0338 permanently closes that owner after its sole 376-call invocation.
  The exact 1,437,835-byte, 378-record real journal contains 376 accepted
  one-call observations, 16 complete adaptive context chains, and no rejection
  or retry. A solver-free result owner reconstructs every policy/dual witness,
  finite-block price, selected branch, teacher counterpart, and all five gates.
  Raise width three is the smallest passing development width: maximum and mean
  normalized full-regret uppers are about `2.286e-4` and `2.377e-5`, while
  conservative aggregate-recovery lower is about `0.977775`. The 16 width-
  three menus are context-local, not one fixed ladder. No elapsed field,
  transfer confirmation, capacity fit, production width, or action exists.
  The next boundary is a value-free untouched transfer pool derived from the
  pre-value ADR-0337 source commit and proven disjoint before any transfer
  qualifier or solver call.
- ADR-0339 passes that value-free transfer-population boundary. Its exact
  pre-value commit seed reaches the first 96 structurally admissible contexts
  after 478 candidates, exposes 13,587 unopened anchored subsets, and has no
  semantic counterpart in the enumerated 1,244-context prior inventory. The
  comparison is a finite absence claim, not representativeness evidence. An
  explicit nonzero-base control also proves that minimum raise-to is converted
  to the historical minimum-bet increment rather than copied through the
  current numerical coincidence. No transfer qualifier, value, width-three
  confirmation, capacity result, or action exists. The next value-bearing
  path remains closed until a separate candidate-blind transfer qualifier is
  source-sealed.
- ADR-0340 passes that source-only qualifier boundary without opening a
  transfer value. It binds the exact 192-task complete-universe-then-width-two
  schedule, unchanged ADR-0323 classifier, first-16 stop, post-`fsync`
  authorization, six distinct semantic terminals, phase-typed infrastructure
  failure, and solver-free target-panel rebinding. Its inherited evidence
  codec still reconstructs real policy and dual witnesses. Synthetic controls
  exercise all terminals; their target panel contains identities only. A
  cross-campaign defect found before seal now rejects a complete wrong-mode
  first record rather than reducing it to an empty prefix. The prospective
  artifact remains absent and the next research act is exactly one retained
  no-clobber invocation from this clean committed source.
- ADR-0341 retains that sole invocation as an exact 378,108-byte, 96-record
  journal. All 94 one-call arms were accepted; the frozen first-16 target was
  reached after 47 complete contexts, with 31 nonqualifiers and no ambiguity,
  rejection, retry, or post-stop call. A solver-free result owner reconstructs
  every policy/dual witness, stop, and unit-correct regret before publishing the
  exact identity-only target panel. The panel is structurally diverse but still
  opportunity-conditioned h4 heads-up fold/call evidence. It does not test
  width three. The next value-bearing boundary is a separately source-sealed
  transfer-confirmation owner that applies the frozen development mechanism
  without width reselection and requires every unchanged conjunct to pass.
- ADR-0342 passes that source-only confirmation boundary without opening a real
  value. It reuses 32 exact ADR-0341 full/width-two arms as prior evidence and
  freezes only 126 prospective width-three candidate calls across the target
  panel. The same candidate values feed the lower-endpoint/smaller-raise direct
  mechanism and the exhaustive interval teacher. Payoff span, chip endpoints,
  normalized regret, reporting equivalence, and the five gate limits remain
  separate semantics. Completed all-conjunct passage and completed scientific
  rejection are distinct from consumer, numerical, unexpected, and
  infrastructure failures. Both complete synthetic terminals and adversarial
  journal controls pass; their fake endpoints are not research evidence. The
  real no-clobber artifact remains absent. The next value-bearing act is the
  sole retained confirmation invocation from this committed source, with no
  retry or width reselection.
- ADR-0343 retains that sole invocation and confirms unrestricted transfer of
  the frozen context-local raise-width-three mechanism on the exact untouched
  16-context reduced panel. All 126 prospective one-call arms are accepted,
  all 16 exhaustive teachers uniquely agree with the direct selection, and all
  five unchanged conjuncts pass: maximum and mean normalized full regret,
  conservative aggregate recovery, and maximum and mean normalized teacher
  excess. The exact 445,731-byte journal and every policy/dual witness, menu,
  context, gate, and terminal rebind through a solver-free result owner. This
  is reduced h4 heads-up fold/call transfer evidence, not a fixed universal
  ladder, responder-raise closure, full-width capacity, production action
  width, complete-decision latency, or poker-strength evidence.
- ADR-0344 source-sealed the first legal responder-raise keystone before
  opening its result. `LegalHeadsUpRiverContinuation` starts after one live
  river check and derives every fold/check/call/integer raise-to action and
  terminal chip settlement from the authoritative six-seat betting kernel.
  The frozen two-live-seat tree distinguishes a full raise-to four after a bet
  of two from the legal short all-in raise-to four after a bet of three; the
  latter is intentionally absent from the legacy simplified sizing game.
  Logical player zero repeats, so the behavioral shortcut must reject and the
  sequence-form generator must match a separate 16-by-18 complete normal-form
  teacher. This one-hand source boundary does not test reopening independently
  and supplies no h4, multiway, capacity, latency, action, or quality result.
  Its sole exclusive-create invocation was the only value-bearing act under
  that authority. `docs/PREDICTION_LEDGER.md` is reporting-only and cannot
  alter any gate or claim.
- ADR-0345 retains that invocation from clean commit `ff2b8ce`. The exact
  7,400-byte artifact passes every frozen gate: six strategic and eleven
  terminal nodes, full and short-all-in branches, zero stored terminal-oracle
  error, repeated-actor shortcut rejection, and agreement between sequence-
  form generation and the independent 16-by-18 complete teacher. The retained
  objective is `2.333333333333333`; realization and retreat errors are below
  `9e-16`. A solver-free owner binds the artifact and every ADR-0344 source.
  The 0.791-second small-game wall is not an action-latency result. Only a new
  h4 legal responder-raise coefficient preregistration is authorized; row
  capacity, selector stability, multiway closure, off-tree actions, full
  width, production action, and strength remain absent. Forecast 2 remains
  reporting-only and open because its capacity and recovery conjuncts are
  unobserved.
- ADR-0307 supersedes ADR-0282's cumulative-street allowance. The authoritative
  hard boundary is 15,000 ms of continuous wall-clock time per controlled
  action, including a fixed 1,000 ms reserve. Older 5-250 ms targets remain
  superseded historical context.
- Belief/topology preparation and speculation before the action clock are
  measured online work. Only an exact semantic artifact hit may be credited to
  a decision, and credited preparation never enlarges its live remainder.
- ADR-0308 implements that contract in the additive `ActionClockLedger`,
  `PreparationBank`, and `LegalDecisionSpineV2`. The exact spine derives the
  current public-state identity, rejects late construction after our turn has
  begun, and forces a legal fallback at the work or wall boundary. The older
  cumulative-street spine remains a historical reproduction control. V2 is not
  yet connected to the complete-hand replay or a live host, and no preparation
  hit has established decision-quality value.
- The frozen measured schedule permits one resident warm step, deterministic
  candidate construction, and only certificates that the deadline guard can
  finish before the reserve.
- Every candidate is compared with the same immutable blueprint anchor. Safety
  does not compose across atomic candidates; any union requires exact
  recertification.
- If no independently certified candidate completes in time, emit the immutable
  blueprint. A late result is unusable.
- Cold construction, warm work, certificate work, persistent GPU-pool bytes,
  physical-free memory, and the emission reserve stay separate in every ledger.
- Every bounded multi-target campaign carries one shared monotonic deadline.
  The runner atomically checkpoints before each frozen target or arm, admits
  the unit only when its complete preregistered bound still fits, and stops
  before any later work or label if either the unit or campaign wall is crossed.
  This campaign ceiling is separate from the 15-second action-response wall and
  from online preparation accounting.
- A speculative cache cannot trust a byte hash first produced by the same
  invocation that consumes it. Population, external hash sealing, and live
  replay are separate prospective stages. Until a later clean config pins the
  complete seed-manifest bytes, every generated entry is unavailable and the
  immutable blueprint remains the completed fallback.
- Every semantic input used to assemble a cached result must be inside the
  externally trusted byte boundary. A cached-row successor may not accept a
  caller-supplied payoff scalar or another numerically plausible substitute.
- A canonical campaign result becomes trusted only after separately bounded
  data and completion-seal phases have built, serialized, exclusively staged,
  published without clobbering, reread, byte-compared, hashed, and passed the
  shared campaign deadline. An exclusive publishing lock keeps partial or late
  states unconsumable; a failed call preserves an unsealed or lock-marked
  diagnostic. Consumers must use the verified loader and never infer trust from
  canonical-path existence.

[ADR-0166](docs/decisions/ADR-0166-prepared-street-fits-two-atomic-certificates-after-one-warm-step.md)
records the current capacity evidence. It does not authorize deployment, claim
a population latency distribution, or establish that the certifiable edits
capture material strategy value.

## Primary measurements

- Exact NashConv and unilateral deviation gains in tractable games.
- Root-strategy harm relative to an exact or dense reference.
- Quality improvement over the blueprint versus wall-clock latency.
- Median and p95 decision latency.
- Nodes touched, peak host/GPU memory, model calls, and data movement.
- Full-game restricted-best-response gain and seat-adjusted cross-play EV.

Iteration count and value-function mean-squared error are diagnostic metrics,
not final success metrics.

## Initial non-goals

- Claiming that the project has solved six-player hold'em.
- Claiming superiority to Pluribus without credible direct evidence.
- Opponent exploitation before a robust baseline exists.
- Distributed training, a graphical interface, or live-site integration.
- Neural models or GPU kernels before exact reference workloads are verified.

## Evidence and dissent protocol

Consequential reviews use: verdict, confidence, supporting evidence, opposing
evidence, largest unknown, cheapest falsifying experiment, kill criterion, and
recommendation. Claims are labeled Known, Reproduced, Observed, Hypothesis, or
Rejected. Tests and measurements outrank either collaborator's preference.

Every ambitious component retains a fallback:

```text
learned scheduler -> heuristic scheduler
adaptive tree     -> fixed tree
neural leaves     -> blueprint continuation
predictive/DCFR   -> LCFR
GPU traversal     -> CPU reference
online resolving  -> blueprint strategy
```

### GPU numerical-identity default

For a Float64 artifact re-derived through GPU or parallel sparse reductions,
semantic identity is numerical by default. Freeze the applicable ceilings
before execution and report digests as diagnostics. The repository defaults
are maximum accumulator and policy-probability error `1e-12`, mean
information-set policy total variation `1e-13`, and maximum quality-vector
error `1e-10`; stricter experiment-specific tolerances may be preregistered.
No tolerance may be introduced or relaxed after observing a result.

A SHA-256 or other bitwise gate remains authoritative for immutable input and
configuration provenance, literal serialized-object identity, immediate
restore/re-export, or an experiment explicitly testing deterministic future
execution. It is not the default semantic-equivalence gate for an independently
recomputed GPU trajectory. Exact discrete fields, schemas, action identities,
and combinatorial work counts remain exact gates unless a preregistration says
otherwise. The executable constants and fail-closed purpose check live in
`pontius.evidence_protocol`.

### Optimization and semantic-type default

A minimization `lower_bound` must come from a dual/Lagrangian certificate with
conservative residual and rounding treatment; a feasible primal objective is
reported as a primal diagnostic or upper bound. Report `U - L` with both
sources and units explicit. Raw solver agreement is not a certificate.

Numerically equal tolerances with different meanings remain separate config
fields and nominal types. Relative reversal, absolute reversal, absolute
optimality gap, selector margin, affine intercept identity, epigraph separation,
resident primal residual, and negative-reach allowances may not share aliases.
Dimensionless probability feasibility may not scale with a chip-valued payoff
cap. Acting and payoff roles are likewise explicit at every cross-payoff
boundary. A root-only affine formula may not be applied to a nonroot public node
merely because the source intercept still matches.

The project is for offline research, simulation, and environments that
explicitly permit automated agents.
