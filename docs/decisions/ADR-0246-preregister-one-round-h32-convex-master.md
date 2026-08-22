# ADR-0246: Preregister one-round h32 convex master

- Status: accepted preregistration before any h32 master candidate or oracle
- Date: 2026-08-22
- Follows: ADR-0245
- Proof: `docs/one-seat-convex-generation.md`
- Config: `experiments/configs/h32-one-round-convex-master-v1.json`
- Config SHA-256: `5d0af4c9ffc54debf3fd6a48d49d7852eba0200b6358c550e081b8bb6e734fdb`
- Sparse master SHA-256: `6c832e5e741bf4b3f2781f637b4a98bc5119eec26fdfefd07146121e850c3bea`
- Sparse master control SHA-256: `1284bbe88053025332a9569076d2cb9f4520f9eb098ebbb99bd714d23e7bc315`
- Runner SHA-256: `69f86e1f946ae65f52780400f969c6365df79ba0e0846de306f6b10613434fc8`
- Runner control SHA-256: `4cc999cc056c3ea85091b98461d99d4bc3fda6629c4af651c63c937c69bd0d0e`

## Question

On the exact ADR-0245 target and acting seat, does the full one-seat convex
program close after its source restricted master and at most one exact
multi-cut round? Can it retain a verified restricted-master lower bound `L`,
an independently evaluated cap-feasible upper bound `U`, and a useful `U - L`
gap while fitting both the measured and corrected conservative 15-second
ledgers?

This is a label-free optimizer and engineering test. It does not ask whether
the candidate is a stronger poker strategy and it emits no candidate.

## Ledger correction

ADR-0244's conservative round formula reserved `500 ms` for the post-cut
master inside a complete cut round, but omitted the initial restricted-master
solve. The parent result therefore reported `13,467.616 ms` for one complete
round when the complete two-master path requires another `500 ms` reserve.

The corrected preregistered reserve is `13,967.616 ms`, leaving about
`1,032.384 ms` under the hard street boundary. The correction is asserted
against the parent's exact identity
`one_round = fixed_before_rounds + complete_cut_round`; inconsistent parent
arithmetic fails closed. One cut round still fits. A second remains forbidden.
No time may be borrowed from the separate final-certificate or emission
reserve.

## Frozen target and axis

Reuse the exact retained Latin-D target
`panel_2/balanced/checks_then_bet_seat1`, its immutable source blueprint, and
acting seat 0. The post-bet continuation must pass the compiled
path-single-visit predicate. The behavioral master must expose exactly 16
acting public nodes, 512 external-hand information sets, 1,024 policy
variables, and six gain epigraph variables.

The normalized guard is `1e-10`. Derive the raw guard only through
`raw_guard(layout, normalized)`, which must equal `3e-9`; neither stack nor pot
may substitute for the game-derived payoff span. Each cap is the exact source
deviation gain plus that raw guard.

## Frozen sparse master

Build exactly six source profile-payoff rows and five source fixed-response
payoff rows with the accepted explicit external-axis contraction. Form one
initial gain row per seat. The acting-seat row uses its invariant best-response
constant; every opponent row is its fixed-response payoff minus its profile
payoff. Retain every exact response row and deduplicate only by exact response
signature.

Solve the restricted epigraph LP with Float64 HiGHS dual simplex over all 512
behavioral simplex equalities. Freeze LP tolerance `1e-10`. Verify primal
equalities, inequalities, and bounds, dual signs, stationarity,
complementarity, and primal-dual objective agreement independently from the
solver success flag. Require all reported primal and dual residual families to
be at most `1e-8`. Any policy reconstruction change above `1e-10` fails closed.
Lower bounds must be nondecreasing within the frozen `1e-8` bound tolerance.

## Frozen oracle and one-round stopping rule

For every master candidate, run all six accepted exact incremental response
evaluations. Do not stop after the first cap or epigraph violation. Compare raw
exact gains with the master epigraph and use `1e-9` as the separation
tolerance.

After the initial oracle:

1. add the fixed response row for every epigraph-violating opponent in one
   multi-cut round;
2. treat an acting-seat violation or a still-violated exact duplicate
   signature as an implementation failure;
3. if at least one row was added, resolve exactly once and run an independent
   final all-six exact oracle; and
4. stop regardless of any remaining violations or gap. If the initial oracle
   has no violation, it is also the final exact oracle and no second identical
   call is charged.

The restricted master objective is `L`. The best exact cap-feasible member of
the immutable blueprint and evaluated master candidates is `U`. Report the
timeout gap only as `U - L`; reject a material reversal and clamp only a
sub-tolerance negative reassociation residual to zero. The candidate is
globally closed for this one-seat scope only if the final exact oracle finds no
epigraph violation and `U - L <= 1e-8`.

## Retreat, measurement, and emission

Construct a factor-`0.5` blueprint-to-incumbent behavioral mixture only as an
interior-retreat diagnostic. Because this topology is path-single-visit, that
mixture is the valid convex realization mixture. Record the Jensen guard-slack
guarantee, but do not certify or emit the retreat.

The measured live ledger charges the warm step, eleven initial row passes, all
master solves, every exact oracle, every new response-row extraction, at least
`50 ms` for retreat/envelope work, and `1,000 ms` for synchronization and
emission. Report row conditioning without approximate deletion, response
signatures, cut targets, active caps, memory pool, physical free memory, and
the complete measured and corrected conservative ledgers. Emit only the
immutable restricted blueprint.

## Promotion and rejection

Authorize a later, separately preregistered one-seat quality trial only if all
identity, topology, provenance, numerical, multi-cut, exact-oracle, memory, and
process gates pass; the one allowed round closes the exact epigraph; the final
candidate is cap-feasible; `U - L <= 1e-8`; and both measured and corrected
conservative ledgers fit 15 seconds.

If one round leaves an open epigraph or material gap, or either ledger exceeds
15 seconds, reject this live convex-master path at current costs and retain it
only for off-clock work or a future independently preregistered cost reduction.
Do not shrink the axis, select a different target, loosen tolerances, or add a
second round after seeing the result.

## Claims boundary

The exact response objective, `L`, `U`, caps, and gap are optimizer witnesses
required to adjudicate convergence. They are not opened as strategy-quality
labels and support no strategy-quality claim. This experiment makes no
multiplayer-safe, deployment, composition, cross-street, population, or broad
poker-strength claim. Any later quality question requires a new clean
preregistration and an independent exact emission certificate.

## Decision

Commit the sparse master, runner, config, controls, this ADR, roadmap, and
generated status from one clean tree before the first h32 master solve or
candidate oracle. Invoke the frozen artifact once with the pinned CUDA runtime
and follow its promotion or rejection branch without adjustment.
