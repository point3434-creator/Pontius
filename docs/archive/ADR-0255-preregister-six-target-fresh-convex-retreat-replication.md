# ADR-0255: Preregister six-target fresh convex-retreat replication

- Status: accepted preregistration before any Latin-E warm step, convex candidate, or final strategy label
- Date: 2026-08-22
- Follows: ADR-0252 and ADR-0254
- Config: `experiments/configs/h32-fresh-convex-retreat-replication-v1.json`
- Config SHA-256: `1bc0176be60bc0db010ac5baa086294d2c151dcb64dce658e78ad1b8d15df6f8`
- Runner SHA-256: `52fb20202d94b0f289718c04a12241674abfd639ea898bc66749f41c57013698`
- Control SHA-256: `5886697cfe4ac3ff962ed18341b46776fe06131d7a101835e37be3a8af81452c`

## Question

Does the one-round, one-seat convex master that produced material certified
value on ADR-0252's known target transfer to a fixed six-target sample of fresh
action-conditioned posteriors while preserving exact per-seat caps and the
complete 15-second street ledger?

This experiment measures fresh shadow transfer only. It does not compare the
convex candidate against a freshly labelled regret-vertex fallback, estimate a
population success rate, or establish a globally optimal one-seat solution.

## Frozen targets and nonselection

Use exactly the six Latin-E rows from ADR-0254 in their manifest order. They
contain one row per retained source context, observed bettor, and acting player,
with three balanced and three blocker-heavy ranges. Acting player remains the
last responder, `(bettor - 1) mod 6`, which gives the frozen 16-public-node,
512-information-set axis.

No marginal-TV, regret, radius, opportunity, source, position, or quality
quantity may select or reorder a target. Every target receives the same
construction. Results from an earlier target cannot change any later target's
actor, factor, rows, cut rule, tolerance, ledger, or acceptance decision.
Promotion is computed only after all six final certificates exist.

The six Latin-F rows remain an unopened confirmatory reserve. This run must
produce zero Latin-F strategy labels.

## Frozen construction

For each target, reconstruct the immutable average-64 source blueprint and its
action-conditioned posterior, then require the pinned source, posterior,
blueprint, hand-axis, and checkpoint identities. Perform one resident DCFR warm
step. Its output does not select or parameterize the convex candidate; the step
is retained and fully charged so the experiment does not understate the current
street pipeline's cost.

Compile the full last-responder behavioral axis: 512 information sets, 1,024
policy variables, and six gain epigraph variables. The path-single-visit
topology gate is mandatory; this behavioral-coordinate shortcut is rejected on
any layout where one seat can act twice on a root-to-terminal path.

Construct all six profile-utility rows and the source best-response gain row for
each seat. The acting seat uses the exact own-BR invariance identity; the five
opponents use explicit fixed-response open-axis contractions. Solve the source
restricted master, project its policy, and spend the first exact all-seat oracle
as an adaptive construction oracle.

Add every newly exposed opponent response facet whose exact gain exceeds the
master epigraph by more than `1e-9`. Response tapes are deduplicated by exact
signature only. Add all violators together, resolve at most once, and do not
run a second separation round. If there are no new rows, retain the first
master candidate. In either case, form the fixed factor-`0.5` mixture of the
immutable blueprint and resulting endpoint.

The first oracle is an explicitly counted adaptive construction evaluation,
not the held-out authority for the emitted retreat. It may add within-target
cuts but cannot influence another target. The second exact all-seat oracle is
the sole final safety and quality label for the half-retreat. Thus the campaign
spends 12 exact all-seat oracles: six construction oracles and six final
retreat labels.

## Fail-closed label barrier

Before opening each final retreat label, require all pinned identities,
warm-start identity, path topology, 512/1,024/6 axis counts, eleven initial
passes, all row identities, first-candidate profile equivalence, LP primal and
dual residuals, policy projection, raw guard, response-signature uniqueness,
all-first-oracle-violator coverage, one-round limit, external-axis splice count,
and retreat simplex mass to pass.

A prelabel failure aborts that target before its final label. The target's
candidate cannot be changed after the barrier. GPU reassociation follows
ADR-0179: the frozen numerical ceilings are authoritative, while immutable
input hashes and blueprint provenance remain exact. No tolerance may be
relaxed after a label.

Keep the cap allowance `2e-11`, epigraph separation allowance `1e-9`, LP and
projection tolerances `1e-10`, and quality allowance `1e-10` semantically
separate. Derive both the raw guard and quality normalization from
`layout.game.payoff_span` through the shared helpers. With span 30 and normalized
guard `1e-10`, the raw guard must be `3e-9`; the stack field is not a payoff
span.

## Exact acceptance and abstention

For every target, set each seat's cap to its immutable-blueprint deviation gain
plus the raw guard. Shadow-accept the half-retreat only if the independent final
oracle establishes all four conditions:

1. exact cap feasibility under the separate `2e-11` allowance;
2. exact NashConv improvement above `1e-10`;
3. minimum exact cap slack of at least
   `(1 - 0.5) * 3e-9 - 2e-11 = 1.48e-9`; and
4. both the measured and effective conservative ledgers fit 15 seconds.

Otherwise abstain to the immutable blueprint. The run is development-shadow
only even on a pass: every actual external policy remains the blueprint and no
candidate is emitted.

The endpoint receives no second post-cut oracle. If no cut is needed, the first
oracle incidentally evaluates that endpoint; otherwise it does not. In neither
case does this bounded one-round construction claim complete epigraph
separation, a global one-seat optimum, or a certified optimizer gap. The final
retreat oracle authorizes safety only for the policy it evaluates.

## Complete wall-clock and memory ledger

Measure cold construction as an experimental-health diagnostic but charge the
resident street path exactly as follows: one warm step, all eleven initial row
passes, every master solve, the first exact oracle, all generated cut rows, the
final retreat oracle, at least 50 ms for retreat/envelope work, and the fixed
1,000 ms synchronization and action-emission reserve.

The measured live ledger must fit 15,000 ms for acceptance. The effective
conservative ledger is the larger of the target's measured total and the frozen
ADR-0247/0252 complete ledger, `13,967.6157 ms`; it must also fit. Record the
component times, cold setup, pool total, and physical GPU free memory. Process
health ceilings are 12 GB pool, 1 GB physical free, 60 seconds per major phase,
and 1,200 seconds total. A late but otherwise safe candidate is a valid negative
scientific result and must abstain rather than invalidate the campaign.

## Promotion rule

Call a target material only when it shadow-accepts and its exact value is
strictly greater than `0.001`. This floor was fixed before Latin-E labels and is
below the smallest accepted one-step value in ADR-0235 (`0.00131707`); it is an
engineering materiality threshold, not a significance test.

Authorize only a separate preregistration for Latin-F confirmation when:

- at least four of six Latin-E targets are material;
- the material set includes both balanced and blocker-heavy ranges; and
- all six targets fit both measured and effective conservative schedules.

Any other clean outcome retains ADR-0252 as known-target evidence and leaves
Latin-F unopened. The threshold, breadth rule, and held-out panel cannot change
after seeing Latin-E.

## Claims boundary

A positive branch may establish only that this frozen one-round half-retreat
produced fresh exact safe shadow value with the recorded breadth and timing on
these six reduced-h32 continuations. A negative branch is equally interpretable
and rejects confirmation at this design point. Neither branch establishes
population performance, full-game safety, multi-seat composition, cross-street
validity, exploitation, deployment strength, global one-seat optimality, or
broad poker quality.

## Decision

Commit the runner, config, controls, this ADR, roadmap, and generated status
from one clean tree before the first Latin-E warm step. Run the frozen artifact
once through the repository `.venv`; CUDA DLL discovery must use the automated
ADR-0248 bootstrap. Audit and seal the result before either authorizing or
rejecting a separately preregistered Latin-F confirmation.
