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
showdowns, joint combo beliefs, and the one-bet state machine;
`river_oracle` independently solves its normal form; `river_context` creates
board-grouped range families; and `river_opportunity` records causal regret and
policy traces against hidden exact labels. Normalized positive regret mass is a
promising pilot ranking feature, not yet a scheduler.

River cache identity has two levels. `structural_digest` covers the public board
and betting structure and may key immutable topology or showdown work.
`provenance_digest` adds the entire normalized joint range and is required for
an exact deployable strategy hit. Approximate belief matches never cross that
boundary: they may seed a solver, but the candidate must be recomputed or
recertified under the current joint range. Root total variation bounds only the
value of a fixed policy and does not imply conditional-range, best-response, or
equilibrium stability.

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
