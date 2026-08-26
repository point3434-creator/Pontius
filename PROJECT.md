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
- ADR-0346 source-seals the next legal responder-raise coefficient gate while
  leaving every result unopened. It widens only the ADR-0345 private axes to
  h4: 16 legal dyadically weighted deals, 12 acting information sets, and 32
  repeated-actor sequence variables. The Float64 open-axis traversal is the
  subject; a separate Fraction sequence/utility/terminal enumerator is the
  teacher. Four payoff and two gain rows retain all 32 coefficients beside
  exact numerators and denominators and are checked at six frozen acting
  policies. Source response tapes are frozen once; endpoint selector
  recomputation is structurally absent rather than represented by a tolerance
  or self-declared gate. A pass can only preregister responder-row growth. It
  cannot establish capacity, selector stability, full width, action-clock
  latency, production action, or quality.
- ADR-0347 retains the first and only clean invocation. Its 100,710-byte
  artifact passes all 34 gates. Four payoff and two gain rows expose 192 exact
  coefficient comparisons, and six acting endpoints across three fixed
  response contexts expose 36 exact affine/direct comparisons; every retained
  error and mismatch count is zero. The solver-free owner independently
  rederives reduced Fraction/Float64 identity, profile zero-sum, endpoint
  utilities, and gain-row algebra without a runner, game, evaluator, teacher,
  optimizer, or write path. The result authorizes only a separately sealed
  responder-row-growth experiment. It supplies no selector, capacity, latency,
  action, full-width, or quality result.
- ADR-0348 source-seals that responder-row-growth experiment before opening
  any h4 target trajectory. The unchanged h4 fixture, dyadic source policy,
  two inherited initial response signatures and exact gain rows, guard,
  tolerance, and 128-iteration ceiling are frozen. A read-only observer wraps
  one production generator call and retains every full signature, generated
  row, master diagnostic, oracle count, conditioning value, and canonical row
  byte. A separate Fraction pass checks fixed-tape coefficients, candidates,
  caps, convergence classifications, and the retained incumbent without any
  out-of-band selector call. The 60-second subject and 120-second total walls
  are infrastructure guards, never action latency. Every h4 growth value,
  selector-stability result, action, full-width result, and quality claim
  remains unopened until the sole committed invocation.
- ADR-0349 retains that sole invocation from clean commit `c807232`. All 25
  gates pass in 1.233 seconds. The two inherited exact response rows converge
  in one 18-pivot master with zero generated rows, exact finite-fixture
  NashConv `27/64`, final gap `2^-53`, zero coefficient/evaluation error, and
  exact oracle accounting. The responder tape changes at the candidate but
  has exact gain zero, so it creates no cut; this observation is not a
  selector-stability result. A solver-free owner rebinds the complete 50,963-
  byte artifact and rejects fully rehashed row or tape corruption. The 0.686-
  second subject campaign is infrastructure, not action latency, and the
  finite objective is not strategy quality. Only a separately preregistered
  selector-window successor is authorized.
- ADR-0350 source-seals that successor without opening an h4 target selector
  value. Four selector-free sequence-form directions have live downstream
  provenance: three public-block one-step DCFR regret vertices and the
  reconstructed ADR-0349 restricted-master proposal. For each player, a
  Fraction oracle charts the exact one-dimensional best-response normal fan
  as `fixed`, `tie_unresolved`, or `switched`; exact unresolved interval
  measure and zero-measure tie points are first-class outputs. Complete total-
  function tape identity alone gates certificates, while reachable-support
  identity and phantom downstream switches remain reporting-only. Every ray
  must reproduce the old exact margin-over-closing-slope breakpoint, and every
  fixed-tape gain row must sit below the maximum best-response envelope with
  the master epigraph direction `z >= row`. The untouched 17-point dyadic
  schedule requires exactly 136 production selector calls. Its 60-second
  selector and 120-second total walls are infrastructure guards, not action
  latency. A pass can authorize only a separately preregistered h4 selector-
  stable affine integration gate; full width remains a parallel lane.
- ADR-0351 retains the sole 1,493,122-byte invocation but rejects its recorded
  integration authority after mandatory interpretation exposed a semantic
  gate defect. The exact map is valid: all eight fan sections, 136 production
  selector values, legacy breakpoints, fixed-tape rows, maximum envelopes, and
  independently checkable identity arithmetic rebind; source-reachable-only
  columns remain authenticated to the sealed mapper because v1 omitted each
  pointwise pruned source tape. But all four acting-player sections have reachable
  tie-unresolved measure one while the v1 certificate helper returned scale
  one. It counted the zero margin and then let a nonclosing slope bypass the
  fail-closed source-separation requirement. The corrected result owner
  reports four violations, `corrected_certificate_pass: false`, and no
  successor authority. `selector_window_v2` structurally checks every source
  margin against its reserve before consulting slope; a tie or reserve overlap
  returns zero. The byte-preserved v1 helper is closed to new consumers. Next
  preregister a tie-aware active-row-envelope recovery, not a single stable-
  tape integration; full width remains a parallel lane.
- ADR-0352 source-seals that recovery without opening its public h4 result.
  The exact small-game oracle takes the bounded Cartesian closure of every
  local Fraction maximizer at each fan boundary and open-cell witness,
  rechecks every complete total tape, and retains every affine gain row even
  when multiple tapes share one row. A typed adapter reserves
  `selector_window_v2` for exact singleton sources; tied sources require zero
  v2 windows and the complete maximum envelope. Every scheduled identity pair
  serializes both source and current pruned tapes, so total-function and
  reachable-support identity can later rebind independently; only total
  identity has certificate authority. Synthetic crossing, positive-measure
  tie, and repeated-actor controls pass. The same-fixture h4 runner remains
  uninvoked, its result path absent, and any later pass is development
  integration rather than untouched confirmation because pre-seal alternate-
  tape reconnaissance is disclosed and excluded from the gates.
- ADR-0353 retains the first and only ADR-0352 terminal as a bounded scientific
  rejection. The clean invocation wrote a 961-byte artifact after the exact
  local-maximizer Cartesian product exceeded the frozen 256-tape per-sample
  bound. It serialized no completed section, row, adapter decision, envelope,
  or target cardinality. The runner is permanently closed; increasing the
  bound and replaying would be a post-outcome relaxation. A solver-free owner
  binds the failure and complete source closure. The next source-only recovery
  must represent the total active choice set factorially, keep reachable
  identity descriptive, and prove a compact affine-row quotient against
  exhaustive controls before any separately preregistered h4 diagnostic.
- ADR-0354 source-seals the representation successor without opening an h4
  target. `exact_directional_face_oracle` computes the complete active face's
  minimum and maximum exact directional slopes in two independent
  lexicographic backward passes; it never materializes a response-tape
  product. The exact total-function cardinality and the reachable-support
  quotient are separate arbitrary-precision columns. A logical-work ledger
  proves operations linear in the explicit tree and reports integer bit
  lengths; a 30-level control represents 1,073,741,824 total tapes over 61
  nodes with zero tapes materialized. The existing exact normal fan remains
  the ray instrument, so a composed future-crossing control detects an
  initially dominated row crossing at `1/2`. A conformance registry now makes
  the applicable tie controls mandatory for every named consumer. Float64 tie
  counts are explicitly uninformative about structural uniqueness in either
  direction. Next preregister a new exclusive legal h4 directional-face
  diagnostic; do not call the closed ADR-0352 runner. This source seal is not
  target, latency, full-width, quality, or strength evidence.
- ADR-0355 preregisters the first legal h4 use of that calculus while keeping
  every target outcome closed. The exact inherited workload is four already-
  retained directions by two target players, with eight fan/face compositions
  and 136 point-face calls on the unchanged 17-point dyadic schedule. Every
  factor, both arbitrary-precision cardinalities, both slope-extremal tapes,
  the work ledger and bit lengths, complete fan geometry, and their seam are
  serialized. Target cardinality, ties, crossings, slopes, and cell counts are
  outcomes, never expected gates. A dirty tree fails before target work and
  the absent result path accepts only one exclusive terminal. The explicit-
  tree and fan-piece guards remain distinct from face cardinality. ADR-0355
  also prospectively corrects ADR-0354's one miscomputed metadata hash: the
  scratch command edited literal `\r\n` source text instead of line endings;
  the mechanism manifests and passing controls were unaffected. Next invoke
  once from the clean source commit. No target, action-clock, full-width,
  quality, or strength result exists at this checkpoint.
- ADR-0356 retains the sole clean invocation and independently rebinds its
  3,888,072-byte artifact without scientific imports. All 20 gate entries,
  eight sections, 136 scheduled calls, and 164 total face observations pass.
  The largest factorized face contains 104,976 total-function tapes with only
  one reachable-support behavior; the aggregate reachable maximum is two and
  the work ledger reports zero materialized response tapes. The exact fan has
  two crossings at the inherited `15/19` and `139/163` breakpoints. Its
  roughly 59-second bounded diagnostic walls cover the full campaign, not one
  decision or solve. This finite same-fixture development result authorizes
  only a separately preregistered tie-aware affine integration successor and
  supplies no full-width, 15-second, quality, or strength evidence. Its exact
  artifact path is `-text`, preserving the retained SHA across checkouts.
- ADR-0357 source-seals the factorized tie-aware affine consumer while every
  new legal h4 integration value remains unopened. The exact normal fan owns
  the complete ray and the two-pass factorized face owns each point. Exact
  source ties dispatch directly to a maximum envelope with zero fixed-tape
  Float64 scores; exact singleton sources alone call selector-window v2. The
  consumer rederives both cardinality columns, checks the interior and
  one-sided endpoint slope seams, proves the exact `z >= row` epigraph direction,
  and rejects Cartesian materialization. Synthetic controls integrate 4,096
  total functions without tapes and preserve repeated-actor total/reachable
  identity. This is source-only mechanism evidence; a separately
  preregistered h4 owner and later untouched confirmation remain required.
- ADR-0358 preregisters that exclusive four-direction/eight-section legal h4
  owner while every target outcome remains unopened. It rebinds each retained
  ADR-0356 section digest, requires nominal tie/singleton dispatch, the complete
  exact maximum epigraph, separate total/reachable cardinalities, zero
  materialized tapes, semantic section identity, and zero action or quality
  output. Its subject time is honestly the sum of the eight live integration
  builds rather than surrounding plumbing. No natural mode, window, piece,
  crossing, cardinality, or runtime is gated. The absent `-text` result path
  accepts one exclusive terminal from a clean commit; a pass remains inspected
  same-fixture development evidence and can open only untouched confirmation.
- ADR-0359 retains that sole terminal. Four exact source ties dispatch to the
  factorized envelope and four singleton sources dispatch to positive v2
  windows; all 22 gates pass with zero materialized tapes and no action or
  quality output. The artifact distinguishes 12 fan rows from ten compact
  interval pieces, including two endpoint-only tied rows. Its standard-library
  owner independently rebuilds source-face algebra/cardinality/work, the
  compact convex envelope, seams, dispatch, aggregates and gates. Non-source
  point factors, non-quotient row residuals, and the live reproduced-section
  digest remain explicitly authenticated-only because the preregistered schema
  omitted their raw inputs. Fresh untouched confirmation must repair that
  schema limit before any new value opens.
- ADR-0360 repairs the prospective schema and source-seals the untouched
  population without opening any new direction or target value. It takes the
  first four SHA-derived card/range contexts from the clean pre-result ADR-0358
  commit with no outcome filter, skip, replacement, or reseed; binds exact
  dyadic ranges, legal h4 state, full-support source policies, normalized
  semantic non-overlap with the single exposed development fixture, three
  fixed regret-history vertices plus one audited converged row-growth proposal,
  and 32 expected sections. Every non-source factor, fan row and exact
  epigraph residual must be serialized. One failed context or section rejects
  the whole future confirmation; no partial pass or abstention is implied.
- ADR-0361 preregisters the sole exclusive owner over that population without
  opening a fresh target. Its downstream compiler exactly rebinds every
  row-growth response row, evaluation, cap and master certificate; its complete
  serializer retains every source and non-source face, fan row, compact piece
  and row-by-point residual. Natural endpoints, ties, modes, geometry,
  cardinalities and timings remain observations rather than gates. The absent
  `-text` result path accepts one clean-commit `O_EXCL` terminal only; the
  32-build laboratory walls are not action-clock or full-width evidence.
- ADR-0362 retains the sole 7,361,728-byte first terminal as the rejection it
  recorded and permanently closes the ADR-0361 writer. A standard-library
  result owner independently reconstructs all 32 complete sections and the
  exact fan, face, cardinality, work, row-growth, epigraph, compact-envelope,
  coordinate, timing, emission, and gate semantics serialized in them. Every
  intended scientific conjunct passes. The sole false recorded gate comes
  from a chained comparison that compares the correct zero/null emission
  mapping to `True`; the artifact emitted no action or quality label. ADR-0361
  is not retroactively relabeled. ADR-0362 separately accepts fresh finite h4
  mechanism evidence and leaves literal full-width capacity, the 15-second
  action clock, multiway closure, action quality, and strength unproved.
- ADR-0363 source-seals the independent literal full-width river capacity
  owner; its result path remains absent. The label-free target carries the
  accepted 1,225/1,081/1,035/990 five-opponent axes to a fixed-hero six-seat
  river showdown. An exact pre-allocation ledger prices the current explicit
  three-seat-half FactorTT arrays before any target allocation, then admits one
  scalar check, one resident prime, and one identical warm leaf contraction
  only if fixed host/device caps and live reserves all clear. A reduced GPU
  control exercises that complete path. The warm unit is not a CFR iteration,
  solve, or action. Pre-seal static target-shape reconnaissance is disclosed
  and excluded from the outcome-neutral config and gates. Invoke the owner once
  from its clean commit; retain any capacity rejection or typed failure without
  retry, and do not infer strategy quality or authorize truncation.
- ADR-0364 retains that sole 798-byte first terminal and permanently closes
  the ADR-0363 owner. It is a pre-capacity plumbing rejection:
  `GetProcessMemoryInfo` failed during the first runtime snapshot, before the
  reduced GPU control, street inventory, allocation ledger, admission guard,
  topology, or contraction. The artifact contains no control or target fields
  and therefore answers no capacity question. Independent typed PSAPI and
  Kernel32 calls both succeed with the same 80-byte structure, isolating the
  untyped 64-bit ctypes ABI as the binding defect. A separately source-sealed
  v2 owner with a new exclusive path is required; v1 is never patched or run
  again.
- ADR-0365 source-seals that additive v2 owner while every new capacity value
  remains unopened. An explicitly typed Win64 module binds both PSAPI and
  Kernel32 plus a same-PID PowerShell sampling control; its 512 MiB allowance
  is telemetry-skew-only and cannot alter capacity or action gates. The v2
  overlay hashes ADR-0364, the exact v1 config/runner/result, the allocation
  model, the new ABI source, owner, and controls, then delegates only to v1's
  unchanged reduced control and target functions. Its new `-text` result path
  is absent. Invoke v2 once from the clean source commit; v1 stays closed.
- ADR-0366 retains v2's sole 11,602-byte passing terminal and closes both
  capacity owners. The current representation is rejected before allocation:
  its exact numeric-array lower bounds are 249.486 GB base, 437.434 GB
  bidirectional, 202.627 GB even under the optimistic scalar ordering, and
  14.679 GB for the resident belief. All five cap/reserve conjuncts reject and
  all target/protocol gates pass; zero target contractions execute. This kills
  explicit compatible-half assignment storage, not literal full width under a
  different exact representation. The next gate is non-enumerative exact
  card-conflict elimination. Truncation remains separately uncertified.
- ADR-0367 prospectively freezes the occupied-card quotient algebra before an
  implementation or target. A directional quotient is valid only when every
  source-half seat is fully summed and every open private-hand axis is on the
  query/right half; target-specific alternation must enforce that precondition.
  Three labeled opponent pairs quotient from 733,055,400 assignments to
  8,145,060 six-card masks, and two pairs from 893,970 assignments to 148,995
  four-card masks. Exact inclusion-exclusion needs containment keys only
  through four cards in this 6/4 seam, but that arithmetic is not a complete
  allocation or latency result. The next source-only keystone must match dense
  and current FactorTT/open-mode oracles, the exact transpose, source-seat
  permutation, fixed-card projection, and topology-stable one-seat refresh.
  No literal full-width target or truncation mechanism is open.
- ADR-0368 seals that bounded exact oracle. Seven quotient controls plus 17
  inherited contraction controls pass: exact literal forward and labeled-
  record transpose/dot-product identities; deterministic small-universe
  properties; byte-identical three-source-seat permutation and topology-stable
  one-seat refresh; safe fixed-card projection; invalid-scope rejection; and a
  six-seat two-component rank-three differential against dense and current
  `left_to_right` FactorTT open mode. Its finite poker source quotients 630
  labeled records to seven masks at multiplicity 90. The implementation still
  stores bounded labeled records and is not a scalable runtime. Next derive
  complete full-width persistent/scratch/work/placement bounds under a
  separate source seal; no device or full-width target is authorized. The
  1,733-test repository audit passes 1,732 with two expected skips; its sole
  failure is ADR-0365's immutable pre-invocation absence assertion encountering
  ADR-0366's correctly retained result. That hash-bound lifecycle defect is
  recorded, not edited or generalized into a failure waiver.
- ADR-0369 prospectively freezes the separate preallocation model. The runtime-
  shaped matrix has 8,145,060 six-card source occupancies and 893,970 labeled
  four-card query records; its adjoint is the same matrix transposed, not a
  fixed reverse split with an open source seat. Combination ranks make source
  masks and sparse incidence implicit, while 32,768-source and 65,536-query
  chunks bound scratch. The model must price the exact fixture width of 176,
  the safe 2,971-column feature envelope, structured automata, forbidden tensor-
  train export, results, refresh, both operator directions, and every named
  host/device array. A source-seat refresh is explicitly a full arithmetic
  rebuild. No operation count may be converted to the 14-second compute wall;
  no device source or literal full-width target is authorized.
- ADR-0370 seals that arithmetic model. The exact fixture has source rank 175,
  width 176, 15.159 MB persistent host/device arrays, and a 492.449 MB device
  peak after separately pricing source, forward-query, and adjoint phases. A
  safe width-2,971 feature envelope peaks at 8.126 GB device and 3.185 GB host,
  so both fixed cap/reserve gates pass. The direct structured automaton replaces
  an explicitly priced but forbidden tensor-train export. Memory is no longer
  the immediate blocker for this layout; 81,711,241,920 dense containment
  additions per cold/source-refresh pass are the binding unmeasured throughput
  risk. No GPU, live-memory, latency, complete-action, quality, truncation, or
  strength claim follows. Standard discovery ran 1,747 tests: 1,744 passed,
  two skipped, and only the already sealed ADR-0365 result-absence lifecycle
  predicate failed after encountering ADR-0366's retained result.
- ADR-0371 prospectively freezes the bounded GPU quotient keystone before its
  source exists. A cardinality-layer zeta recurrence computes the same exact
  containment marginals with 55,619,730 vector edges on the 45-card geometry,
  or 9,789,072,480 scalar additions at fixture width 176; this is logical work,
  not a measured speedup. The only natural device population is the complete
  ten-card reduced universe. Direct structured-automaton consumption, the
  sunk/reach affine fold, forward/adjoint identity, topology-stable full source
  refresh, deterministic warm output, independent numerical envelopes, exact
  work counters, mutation controls, and reject-before-CuPy preallocation are
  conjunctive. No literal 45-card allocation or timing is authorized.
- ADR-0372 seals that complete ten-card mechanism on the RTX 5080. All 22
  numerical, exact/current-stack, forward/adjoint, affine-fold, permutation,
  full-refresh/query-only, repeatability, allocation, work, and mutation gates
  pass. Worst forward absolute error is `6.228351168147128e-14`; cold/warm/
  source-refresh four-phase device sums are 0.4435/0.2958/0.4346 ms on the
  reduced population. Those are bounded CUDA-event units, not a target or
  action estimate. A semantic correction compares the current normalized chip
  value rather than non-invariant raw factor scales. Next preregister a non-45-
  card staged scaling ladder; literal capacity and truncation remain closed.
- ADR-0373 prospectively freezes that staged ladder before source or device
  calls. Complete 10/16/22/28/34/40-card axes use one direct-automaton component
  with source rank 127 and width 128. Cold, five warm, three full source-
  refresh, five query-only, and one-plus-three unique-adjoint observations are
  separately timed and ledgered per stage. Direct source/query samples,
  affine rows, full forward/adjoint dot products, byte identity, live/fixed
  admission, durable first-terminal evidence, 120-second stage and 600-second
  campaign stops are conjunctive. The public owner rejects 45 cards; implement
  and source-seal it with the real journal absent before any invocation.
- ADR-0374 source-seals that owner without opening one staged value. The
  complete-axis compiler, lane-specific cold/refresh/query-only/adjoint work,
  all resident unary/factor arrays, exact fixed/live admission, one-thread-per-
  selected-query-feature direct scan, raw repetition identities, append/fsync
  journal, and CuPy-free gate rebinder are hash-bound. Sixteen staged controls
  and the 41-test load-bearing group pass; both real paths remain absent. Four
  pre-result defects—tautological provenance, query-vs-query-feature CUDA
  ownership, two omitted resident unary arrays, and summary-trusting reader
  logic—were repaired before sealing and before any staged call. The next act
  is the sole clean committed invocation; 45 cards, the action clock, quality,
  truncation, and strength remain unopened.
- ADR-0375 retains that sole v1 invocation as pre-journal infrastructure
  failure. The frozen `artifacts/` parent did not exist, so exclusive writer
  creation raised before a header, stage loop, or GPU call. Both result paths
  remain absent, but v1 is consumed and cannot be retried. A successor must be
  additive, use a new result identity, hash-bind a tracked parent artifact,
  and prove the literal public-path bootstrap before any staged call; the
  scientific stage contract remains exactly ADR-0373's.
- ADR-0376 source-seals that additive v2 owner. A tracked `artifacts/README.md`
  is hash-bound by config and verified with exact `git ls-files` provenance;
  the new public path, derived partial, and both permanently closed v1 paths
  are checked before Git or stage authority. Eight lifecycle-aware controls
  pass without a device call, including missing/drifted/existing bootstrap,
  exclusive replay, first rejection, durable exception, torn/mutated journal,
  campaign-envelope identity, and distinct before/after-stage wall seams. The
  six stages and every ADR-0373 scientific field are unchanged. Invoke the
  clean v2 owner once next; no staged observation exists at this source seal.
  Full discovery ran 1,785 tests: 1,782 passed, two optional tests skipped,
  and only the already retained immutable ADR-0365 result-absence predicate
  failed against ADR-0366's retained result.
- ADR-0377 retains the sole v2 invocation as a complete six-stage pass. All
  126 gates reconstruct true through 40 cards; requested peak storage grows to
  10.046424 GB while live free memory remains 15.710814 GB and device pools
  return to zero. At 40 cards the production-relevant cold/warm/full-refresh/
  query-only/adjoint medians are 361.201/327.622/296.192/32.319/1,015.458 ms;
  the independent direct-scan oracle takes 49,557.238 ms and dominates the
  59,661.607 ms stage wall. These are non-target lane units, not a solve,
  action, or 15-second result. Next freeze literal-45 production and validation
  lifetimes separately plus streamed-validation identity before any target
  allocation; truncation remains an independent hypothesis.
- ADR-0378 prospectively freezes the literal-45 liveness question before any
  target code or allocation. Production arrays, complete host-held validation
  references, 64-MiB chunk staging, streamed dot scratch, and post-forward
  adjoint arrays receive distinct semantic roles and phase lifetimes. Full
  device output copies, simultaneous forward/adjoint state, a full dot-product
  temporary, and digest-only repeatability are forbidden. Implement a CuPy-
  free lifetime sweep and bounded chunk controls next; no capacity verdict is
  open at this preregistration.
- ADR-0379 seals that pure model. A phase sweep prices the 45-card forward at
  10,772,495,644 bytes, the streamed-dot device peak at 11,755,029,796 bytes,
  the post-release adjoint at 9,645,290,380 bytes, and the host peak at
  9,353,336,216 bytes. Fixed caps and minimum-physical reserve arithmetic pass,
  but only 244,970,204 device bytes remain under the numeric cap. The old
  validation schedule rederives at 20.349 GB before a possible 915 MB product
  temporary. Next prove the new seam and allocator high-water on bounded CUDA
  populations; no literal allocation or action result exists.
- ADR-0380 preregisters that bounded CUDA seam before device source. It fixes
  the complete 10/22-card populations, forces the 22-card source reference
  across two 64-MiB chunks, permits one overwritten active-unary buffer, and
  requires complete literal-byte references, streamed host dots, forward-state
  death before unique-adjoint birth, and raw allocator/free-memory telemetry at
  every transition. Every other width, including 45, must reject before CuPy
  import. A pass can authorize only a separately sealed one-shot target owner;
  it cannot establish target capacity, timing, action quality, or truncation.
- ADR-0381 seals the bounded result. Every 10/22-card gate passes: complete
  ten-card exact forward/fold/adjoint errors stay below `2.1e-15`, the 22-card
  source crosses the 64-MiB seam in exactly two chunks, forward and reverse
  dots agree within `5.7e-14`, and the largest pool total is 204,377,088 bytes
  under a 271,464,560-byte model. Forward state is observably dead before the
  unique adjoint is born, and pools plus physical free memory return exactly
  to baseline. The pre-seal reverse-work formula's 63-versus-57 subset defect
  is recorded; no scientific setting changed. Next preregister a separate
  one-shot literal owner—45 remains uncalled.
- ADR-0382 freezes that future one-shot boundary before target source. It binds
  the exact 45-card geometry, 9.353 GB host and 11.755 GB device lifetimes,
  fresh live admission, 125 source chunks, independent target sample ranks,
  one exclusive/fsynced journal, five permanent terminal classes, and absolute
  allocator release. The source-seal tests may use only injected synthetic
  outcomes; no literal target allocation or value is open.
- ADR-0383 source-seals the inert owner and independent standard-library
  reader. Fresh imports leave CuPy absent and all target counters zero; 35
  ordered named numeric births, 19 scientific calls, exact ownership transitions,
  nonnegative error intervals, and infrastructure-only wall/release failures
  are mechanically controlled. The public result remains absent until one
  post-commit no-argument invocation.
- ADR-0384 permanently consumes that owner and retains a 21,663-byte
  `completed_pass` journal. All 27 independently reconstructed gates pass;
  maximum pool total is 11,620,834,304 bytes and both pools release to zero.
  This establishes one literal full-width river quotient primitive on the
  named workstation, not an actual poker-context bridge, solve, action,
  15-second decision, quality result, truncation authority, or strength.
- ADR-0385 preregisters the first actual-context adapter without opening a
  full-width value. One six-way checked river binds an action-conditioned
  five-opponent 990-combo belief to the quotient's logical axes. Exact
  integer-chip identity is limited to a single 60-chip flat pot; odd chips,
  unequal sunk contributions, and side pots reject before automaton use.
- ADR-0386 source-seals that adapter with CuPy absent. The complete host
  fixture has rank 175, width 176, and 893,970 query labels. The reduced seam
  has zero chip error per legal deal, exact literal forward/transpose
  identities, and sub-`2e-11` inherited-consumer differentials. No full-width
  quotient value, solve, action, 15-second result, or quality claim exists.
- ADR-0387 preregisters the actual-context consumer-capacity seam before its
  source or any value. The exact global feature partition is 128+48, with
  reach at global index 175 owned once and conditional normalization forbidden
  until partial numerator/reach recombination. Forward streams 65,536 labeled
  records; adjoint streams 10,922 complete six-label occupancies rather than
  reusing that numerical knob. Named lifetime rows, forward-before-adjoint
  release, fixed caps, a complete ten-card rank-175 exact differential, and
  allocation/semantic mutations are frozen. No CuPy, capacity verdict,
  full-width contraction, iteration, action, timing, or quality result exists.
- ADR-0388 source-seals the CuPy-free capacity answer. Every aggregate bridge
  class expands into 58 named physical rows; independently swept host/device
  peaks are 15,973,968 and 9,910,940,332 bytes, and all fixed cap/reserve
  inequalities pass. Complete exact ten-card rank-175 monolithic-versus-128+48
  forward/fold/adjoint, reversed-order, chunk, normalize-once, and transpose
  controls pass. Live allocator admission, device execution, every 45-card
  quotient value, solve, action, 15-second result, quality, and truncation
  authority remain absent.
- ADR-0389 preregisters the actual-context CUDA-consumer boundary before
  source or device values. The new additive module must use globally
  offset-aware 128+48 kernels, complete-label and source-occupancy streaming,
  one post-slice normalization, deterministic reductions, 25 named numeric
  births, contemporaneous live admission, and complete ten-card plus
  multi-chunk 25-card device differentials. Its inert one-shot owner and
  solver-free reader are source-seal work; the actual 45-card result path
  remains absent and unauthorized until a later clean committed invocation.
- ADR-0390 refuses that source seal on its sole red conjunct. Complete ten-card
  CUDA conformance passes, and the complete multi-chunk 25-card population has
  byte-identical default/alternate rows and scalars plus passing exact source,
  independent forward/fold/adjoint, offset, poison, repeat, allocation,
  release, and wall controls. The 25-card forward numerator
  `0x1.9a7e7b97a67d1p+32` and transpose
  `0x1.9a7e7b97a67d0p+32` differ by one ULP (`0x1p-20`): the relative envelope
  passes, but ADR-0389's distinct `2e-10` absolute conjunct rejects. The
  tolerance stays frozen, all actual counters stay zero, and no owner or
  45-card artifact exists. A successor must preregister same-memory paired
  high/low feature tiles or another structural arithmetic repair before source.
- ADR-0391 prospectively freezes that repair. Three globally indexed logical
  tiles of widths 64/64/48 map each feature to adjacent high/low Float64
  components in the same 128-column physical workspace. Error-free primitive
  controls, exact `Fraction.from_float(high)+Fraction.from_float(low)` scalar
  authority, canonical global pair trees, temporary reuse, typed work, and a
  predicted 9,910,940,380-byte device peak are fixed before successor source.
  Both original numerical conjuncts and every complete 10/25 semantic,
  byte-identity, runtime, memory, and wall gate remain mandatory. Even a pass
  cannot create an actual owner or 45-card value without another ADR.
- ADR-0392 corrects ADR-0391 before source: zeta recurrences require a frozen
  paired division by exact positive integers, and query weights require an
  explicit mixture/seat/unary/mode multiplication order. The v2 overlay fixes
  a two-residual divide, paired covectors, pair-times-pair forward/transpose
  products, and exact-rational post-tile normalization. It changes no v1
  population, ceiling, memory, wall, or claims gate and opens no result.
- ADR-0393 rejects that paired source seal on capacity before a complete
  25-card numerical result. Strict primitives, query weights, and every opened
  complete ten-card exact-row, transpose, byte, offset, poison, lifecycle,
  mutation, and release gate pass, with a represented residual near
  `1.45e-25`. The first frozen 25-card campaign exceeds its 180,000-ms wall
  and remains nonterminal at the 600,000-ms laboratory stop; no 25-card scalar
  is available. The source is retained, the invocation is closed, and no
  actual owner, 45-card value, resolver/action timing, quality, or truncation
  authority opens. A successor must preregister phase work and clear a
  conservative capacity preflight before another complete 25-card value.
- ADR-0394 preregisters that capacity preflight without opening successor
  source or timing. Source-rank-major direct controls preserve exact pair-add
  order while reducing projected complete-25 direct-fold unranking from
  1,994,854,400 to 34,003,200 visits; the 611,229,696 coefficient additions
  remain priced. Complete 10/22 campaigns, 16 nonoverlapping host phases,
  executed-work counters, fixed exact-work ratios, a 5/4 guard, an exclusive
  one-shot journal, and a CuPy-free reader are frozen. Population 25 is
  arithmetic-only until a later authority, so no 25-card numerical value,
  actual owner, action-clock result, quality prior, or truncation choice opens.
- ADR-0395 corrects the preregistered compiler-resource instrument before any
  result: five caller NVRTC options remain unchanged, the retained payload
  must be ELF, raw CUDA-13.3 `cuobjdump` output is independently rebound, and
  driver/cubin register and stack-plus-local maxima are gated against 255
  registers and 4,096 bytes per thread with explicit device-reserve arithmetic.
  Exact spill traffic remains unavailable and must not be invented. ADR-0396
  source-seals the composite source, exclusive subprocess owner, exact raw
  phase/work ledger, constituent-complete ratio audit, and standard-library
  reader with 18 source/synthetic controls passing. Both result paths remain
  absent; no calibration, complete-25 numerical value, action timing, quality
  prior, or truncation authority opens.
- ADR-0397 retains the sole v1 work-preflight invocation as a durable
  infrastructure failure. The runner spawned `python -m __main__` because it
  derived the child module from runtime `__name__`; resolution failed before
  worker import, CuPy, any 10/22 calibration, or phase evidence. The immutable
  5,322-byte journal has header, clean provenance, and terminal only. V1 is
  permanently closed; only a new-identity additive v2 with a literal worker
  module and real no-CUDA subprocess handshake may reopen the unchanged
  experiment.
- ADR-0398 preregisters that additive v2 before source. Its literal module,
  fresh 32-byte challenge, common Popen/framing/stdout/stderr/deadline/return
  seam, new evidence identities, immutable-v1 binding, and CuPy/science import-
  absence gates are frozen. The source seal must spawn the real handshake child
  without creating the v2 result; injected executors are not bootstrap proof.
- ADR-0399 source-seals the additive owner and solver-free reader. One shared
  bounded subprocess transport serves handshake and campaign; the real fresh-
  challenge control proves literal worker birth with CuPy and science unloaded.
  All 16 focused controls pass and the v2 result remains absent. Only the clean
  committed no-argument owner is eligible for one invocation.
- ADR-0400 retains that sole invocation as a distinct infrastructure failure.
  Bootstrap passed, but a slots `CudaRuntimeIdentity` could not cross the
  `__dict__`-only evidence normalizer while reporting an earlier compiler/
  resource exception. That earlier cause is masked and unclassified. The
  artifact has two lifecycle events, zero phases, and no projection; v2 is
  permanently closed.
- ADR-0401 preregisters v3 before source. It admits exactly one concrete slots
  dataclass through declared fields, forbids generic object conversion, keeps
  the scientific file immutable, and requires a real no-CUDA forced-failure
  child through the scientific `send` closure and shared transport. The exact
  sentinel reason must survive and every patched source identity must restore.
- ADR-0402 source-seals v3 after 16 corrected controls. The exact-type adapter,
  three-mode literal owner, and nested V3-to-V2-to-V1 reader are hash-bound;
  the real no-CUDA probe preserves the sentinel reason and restores every
  identity. No campaign child or v3 result exists at the seal.
- ADR-0403 retains V3's sole call. Literal bootstrap and the exact-type
  serializer probe pass; the real campaign reaches an ELF-loaded cubin and
  then CUDA 13.3 `cuobjdump --dump-resource-usage` returns status 4294967295.
  No raw resource row, calibration phase, or projection exists. V3 is closed;
  any successor must first qualify an exact-cubin inspector under a new
  identity while retaining raw return code, stdout, stderr, and cubin bytes.
- ADR-0404 freezes that diagnostic before source. It permits one future
  unchanged `_kernels` compile only, journals the exact ELF before inspection,
  captures five ordered CUDA 13.3 operations with `check=False`, and keeps
  `selected_inspector=null`. No calibration, population fixture, resource gate,
  projection, latency, action, or quality result exists.
- ADR-0405 source-seals that diagnostic after 15 corrected controls. Parent
  ACK follows durable fsync, the exact cubin precedes every tool operation, the
  laboratory wall includes compilation, and exact prospective journal
  envelopes reserve the outer terminal. Real CUDA diagnostic calls remain
  zero and both result paths remain absent at the seal.
- ADR-0406 retains the sole diagnostic call as a complete 705,101-byte
  capture. The driver loads the 514,039-byte ELF-magic payload and reports all
  three direct-kernel attribute rows, but CUDA 13.3 `cuobjdump` says the file
  contains no device code and `nvdisasm` calls it invalid ELF. Those raw
  outcomes are not interpreted at this boundary: no inspector is selected and
  no resource gate, calibration, population, phase, or projection is open.
  The next step is a prospectively frozen GPU-free selector over only the
  immutable artifact; it must type an empty selection honestly and may not
  substitute driver-only evidence.
- ADR-0407 preregisters that artifact-only selector before source. CUDA 13.3's
  documented per-function `REG`/`STACK`/`LOCAL` output makes only the retained
  `cuobjdump_resource_usage` operation semantically eligible; version, ELF,
  driver, and default `nvdisasm` evidence remain supporting facts. Selection
  requires exact identity, return code zero, and complete independently parsed
  rows for all three direct kernels. `no_qualified_inspector` is first-class,
  and resource ceilings cannot decide whether an instrument is valid.
- ADR-0408 source-seals the standard-library selector after 12 synthetic
  controls. It independently parses complete resource rows, preserves exact
  semantic quantity pairing and componentwise maxima, keeps the resource gate
  null, and proves empty selection under version-pass/resource-fail, all-
  nonzero, ELF/driver-only, and nvdisasm-register-only evidence. The real
  artifact has not been read through the selector and the canonical result
  remains absent at the seal.
- ADR-0409 retains the sole selector assessment as
  `no_qualified_inspector`. CUDA 13.3.73 identity passes, but the only complete
  resource candidate has retained return code 4294967295; all selected,
  combined, resource-gate, calibration, and projection fields are null. A
  separate unsealed design trace finds a one-byte ELF table deficit aligned
  with CuPy 14.2.0's unconditional cubin suffix removal. That is only the next
  bounded hypothesis: no byte has been appended and no repair is accepted.
- ADR-0410 preregisters that one-byte hypothesis before source or operation.
  The exact ELF header, six program rows, section/program bounds, sole zero
  suffix, repaired hash, six external commands, same-byte module load, all
  fifteen names, and exact original driver rows are frozen. A pass can qualify
  only the repaired-byte resource instrument; all 255/4096, calibration,
  capacity, latency, and quality gates remain null.
- ADR-0411 source-seals that diagnostic after 22 synthetic/device-free
  controls and catches one pre-result semantic-coincidence defect: equal
  8 MiB payload and command-stream caps now have separate typed encode/decode
  paths. No real CUDA tool, module load, launch, or result has run. The sole
  next authority is one clean no-argument invocation from the seal commit.
- ADR-0412 retains that sole invocation as `suffix_reconstruction_pass`. The
  exact repaired bytes pass cuobjdump resource/ELF, both nvdisasm payload
  operations, all fifteen module lookups, and original-driver-row equality.
  The repaired-byte resource instrument is qualified; the 255/4096 gate,
  calibration, capacity projection, action, and quality remain null.
- ADR-0413 prospectively freezes the additive work-preflight V4 seam. The exact
  live 514,039-byte compiler prefix must receive its sole zero before module
  load, and the identical repaired bytes must be loaded, retained, and boundedly
  inspected. The ADR-0395 two-instrument maxima and every ADR-0394 population,
  phase, ratio, wall, and integer-only population-25 rule remain unchanged.
  At that preregistration checkpoint, V4 source, resource, calibration, and
  projection evidence were absent.
- ADR-0414 corrects V4's evidence-envelope arithmetic before source. Four
  independently capped command streams are retained in exact chunks under a
  64 MiB journal; smaller strict-ASCII parser-admission bounds protect the
  unchanged 1 MiB child-line event only after raw retention. Capture, parser,
  child-line, and journal limits can no longer substitute for one another.
- ADR-0415 source-seals the composite V4 boundary after 17 focused controls.
  Repair occurs before module load, every raw command chunk is fsynced before
  child progress, and the independent standard-library reader rederives the
  exact ELF identity and driver/cubin maxima before admitting the immutable
  10/22-card, 16-phase science. At that seal, the real V4 result and reserved
  actual result were absent and only one clean no-argument invocation could
  open the next resource/calibration/capacity terminal.
- ADR-0416 retains that sole invocation as `completed_capacity_rejection`.
  The repaired executed cubin, all four resource gates, the complete 10/22
  calibrations, and every numerical and order conjunct pass. The unchanged
  worse-endpoint projection is 7,260.753615922 seconds against 180 seconds;
  no population-25 fixture ran. V4 is consumed. The next boundary is a fresh
  preregistration for structural exact-work reduction in the four phases that
  account for 89.5161% of the projection, not a retry, endpoint substitution,
  wall relaxation, truncation decision, action result, or quality claim.
- ADR-0417 freezes the first such reduction. The selected direct-fold kernel
  already accumulates every coefficient needed by the selected direct-query
  oracle in the identical source-rank order. One shared traversal must emit
  both outputs, deleting 34,003,200 projection-only source unrankings and
  27,783,168 redundant boundary pair additions. Source, controls, device
  differential, owner, result, and replacement capacity rule remain absent;
  implement and source-seal only this exact common-subexpression boundary next.
- ADR-0418 completes that source-only seal. The builder changes exactly the
  direct-fold kernel span, preserves the reference query kernel byte for byte,
  and copies boundary pairs only after full source-rank accumulation. Nine
  focused controls pass with zero CuPy imports, compiles, loads, or launches.
  A new exclusive complete-10 differential and complete-10/22 shared-path
  owner must be preregistered next; no capacity projection is selected.
- ADR-0419 preregisters that device differential without opening source or
  CUDA. Raw compiler bytes must become durable before the sole complete-ELF or
  bounded one-zero container classification; the retained V4 cubin supplies
  complete-10 query/fold byte controls, while complete 10/22 population paths
  launch only the shared fold under a contiguous 15-phase ledger. Slot 9 is
  boundary-feature count and slot 11 is logical width. No projection rule is
  present; implement and source-seal this owner/reader boundary next.
- ADR-0420 completes that source-only seal after 18 focused controls. Raw
  compiler bytes are ACK-durable before an exact complete/one-zero ELF
  classifier, the retained V4 cubin is complete-ten control-only, and generated
  complete 10/22 population code structurally excludes the reference query and
  population 25. The independent standard-library reader reconstructs a full
  86-observation synthetic pass. A pre-evidence review also separates full
  population elapsed wall from summed phase intervals and moves host stamps
  after CUDA synchronization. No real compile, load, launch, result, or
  replacement projection exists. The reader also rejects overlapping family
  walls and binds cleanup without a completed resource command to an early
  failure terminal; one clean no-argument invocation from the
  ADR-0420 commit is next and may never be retried.
- ADR-0421 retains that sole public command as a launcher-resolution failure.
  Repository Python exited `1` with `No module named 'pontius'` before owner
  import because the sealed command depended on an ambient `PYTHONPATH` that
  was absent. No journal, handshake, CuPy import, compiler observation, module
  load, launch, phase, population, or device value exists, and both protected
  result paths remain absent. The ADR-0420 command and result identity are
  permanently consumed. Preregister a new-identity repository-root launcher
  and require a scrubbed-environment handshake through its literal public path;
  do not retry ADR-0420 by setting `PYTHONPATH`.
- ADR-0422 preregisters that launcher-only V2 recovery under a new config,
  protocol, campaign, header, result, owner, reader, and control identity. One
  repository-root script must install the exact sealed `src` path for the
  public parent and every child. Its source seal must traverse the literal
  parent-to-child launcher from outside the repository with `PYTHONPATH` and
  `PYTHONHOME` removed, user site disabled, and CuPy/science absent. Scientific
  event payloads remain V1; the V2 reader may reuse the source-sealed CuPy-free
  V1 semantic reader only behind an independently checked envelope/header
  transduction. Implement and source-seal this boundary with every result path
  absent; do not operate it from the preregistration commit.
- ADR-0423 corrects a pre-source contradiction in that reader contract. A
  fresh bootstrap cannot both report V2 module identity and remain untouched
  for a V1 reader that requires V1 identity. The corrected config independently
  validates V2 lifecycle provenance, then permits only protocol/campaign,
  header, observation-wrapper config, and bootstrap literal/spec identity to be
  projected in memory. Challenge, runtime, CuPy, every post-bootstrap event,
  and the outer terminal remain unchanged. No source or probe existed under the
  rejected config hash; implement only the corrected hash next.
- ADR-0424 corrects three inherited V1 parent hashes after the uncommitted V2
  parent-hash gate rejected them. An over-escaped shell audit had rewritten the
  literal source characters `\r\n` instead of CRLF bytes, reproducing the three
  false ADR-0420 metadata values exactly. The committed V1 files and science
  are unchanged; the corrected V2 config binds their true canonical-LF hashes.
  At discovery the scrubbed launcher probe and 14 of 16 controls passed, with
  zero CuPy/device/result work; the two exact hash controls rejected. Add an
  independent byte-loop hash differential and source-seal only the corrected
  config.
- ADR-0425 completes that launcher-safe V2 source seal. Twenty focused V2
  controls and all 18 unchanged V1 controls pass; the literal root launcher
  crosses the public parent and internal child from an external working
  directory with package-path state scrubbed, while CuPy, the science adapter,
  and every result path remain unopened. The reader validates V2 lifecycle
  identity before projecting its exact ten-path allowlist to the unchanged V1
  semantic oracle. The next authority is one clean no-argument root-launcher
  invocation from the sealed commit, with the first V2 terminal permanent.
- ADR-0426 retains that sole V2 invocation as a population-10 scientific
  rejection. Launch, bootstrap, compiler/container/module/resource plumbing,
  complete-ten, and query-weight controls pass; both population-10 families
  reach final release. Evidence assembly then compares 56 source pairs from an
  inherited seven-row execution sampler with 128 pairs from the frozen 16-row
  evidence sampler and rejects before any population row. V2 is consumed;
  population 22, every projection, and population 25 remain unopened. A fresh
  successor must share one immutable sample plan between execution and evidence
  and prove that binding before CuPy or device work.
- ADR-0427 preregisters that fresh V3 boundary before source. Literal 16-row
  source/query populations and eight boundary features for both 10 and 22 cards
  form one frozen plan object per population. Generated execution and evidence
  must receive the identical object; generated-global identity, ranks, features,
  and all four sample shapes reject before CuPy. V2 remains closed, and the
  source-only checkpoint may add only the fresh adapter/launcher/owner/reader/
  controls and scrubbed no-device launch probe.
- ADR-0428 completes that source seal. Twenty-one focused controls bind the
  immutable plan not only at execution and evidence endpoints but through the
  population-evidence, family-runner, and top-level validation seams. The old
  seven-row helper and rank/feature/shape mutations reject before CuPy; the
  independent V3 reader accepts complete and failure synthetic journals while
  preserving every post-bootstrap event. A scrubbed external-working-directory
  probe crosses both literal launchers without CuPy, science import, or result.
  The next authority is exactly one clean V3 invocation; its first terminal is
  permanent, and the exact-integer proposal remains a separate unimplemented
  hypothesis.
- ADR-0429 retains V3's sole invocation as a complete 10/22 validation pass.
  The independent reader accepts 3,052 records, both population rows, 3,028
  phase rows, exact work and numerical gates, and absolute release. Population
  elapsed validation walls are 9.348 and 49.419 seconds under the frozen
  90-second laboratory ceiling; neither is resolver or action latency. V3 is
  consumed. Before any population-25 or actual-consumer work, freeze a separate
  artifact-only capacity projection; the exact-integer pipeline remains an
  algebra-first hypothesis with no current result.
- ADR-0430 freezes that artifact-only question before source or projection.
  Fifteen device-work components keep the prior maximum-over-endpoints exact-
  ratio rule; the fused shared phase is priced by its complete work constituents.
  A sixteenth component explicitly prices population wall outside the phase sum
  at fixed scope, then every component receives the unchanged 5/4 plus 1 ms
  guard against the 180-second limit.
- ADR-0431 implements and source-seals that assessor without opening its real
  projection. The assessor independently reconstructs all 3,028 raw V3 phase
  rows, both complete work ledgers, and both outside-phase envelopes; its
  independent reader rederives all ratios, candidates, uppers, claims, and the
  terminal. Exact inclusive-wall and envelope-alone rejection controls pass.
  One clean exclusive artifact-only invocation is next; population 25 remains
  geometry only and no CUDA, action, quality, or exact-integer result exists.
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
