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
