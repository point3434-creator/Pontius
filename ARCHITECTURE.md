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

## Current h32 execution spine

The active boundary is a prepared six-player river decision with 32 hands per
seat. Off-clock preparation builds the immutable blueprint, factorized belief
contexts, shared public topology, resident solver state, and incremental
response caches. Allocator scratch is trimmed before the street becomes ready.

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
and finite serialization use `runner_harness`. Byte-pinned historical runners
remain immutable, with their legacy expressions held in an exact AST exception
inventory. New device-fold customers likewise use the non-consuming,
contiguity-guarded `resident_record_to_hand_fold_v2` successor rather than
altering the pinned fold. [ADR-0233](docs/decisions/ADR-0233-shared-payoff-semantics-and-runner-contracts-retire-repeat-defects.md)
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
