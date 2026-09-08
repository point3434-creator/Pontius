# ADR-0317: Separate solver classes and prioritize the certified sizing adapter

- Status: accepted optimization triage and prospective adapter preregistration before source
- Date: 2026-08-23
- Follows: ADR-0316
- Wide-ledger source: `experiments/results/h32-fresh-convex-retreat-replication-v2.json`
- Wide-ledger source SHA-256: `daaad3080637284d5413f156bad5df19256f8e7a36829026076ea38aeae1355e`
- Current-decision source: `experiments/results/h32-decision-aligned-live-shadow-v1.json`
- Current-decision source SHA-256: `e926a64ca5d7ac55086607c3c697c51165777d888767f051359f19bb743b2d4f`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0317
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement and source-seal only a prospective canonical reduced-sizing HiGHS dual-simplex adapter with exact behavioral reconstruction, original-unit feasibility checks, an outward-rounded bounded-variable certificate, typed diagnostics, and fail-closed toy controls; change no v1 consumer, invoke no sealed corpus or candidate value before that source boundary, and keep behavioral-master persistence or specialization parked until a fresh certified v2 complete ledger crosses the frozen materiality trigger
- Front-Door-Blockers: no production reduced-sizing HiGHS adapter or adapter-specific sealed result exists; the legacy sizing oracle still invokes rejected native simplex; historical behavioral-master consumers still use the uncertified-v1 bound label; no fresh action mechanism or panel is authorized; behavioral-master replacement has at most 0.151 percent measured complete-ledger headroom on the retained panels

## Question

Does ADR-0316 authorize one solver-replacement project or two different
questions, and which one has enough leverage to run next?

The native failure that rejected ADR-0310 occurred in the compact reduced
river sizing LP. The proposed product-of-simplexes specialization instead
describes the one-seat behavioral convex master, which already calls SciPy
HiGHS dual simplex. Treating those as one workload would use the timing and
structure of one LP class to justify replacing the solver of another.

This decision performs no LP solve, opens no candidate or strategy label, and
changes no consumer. It reuses two already accepted complete-ledger artifacts
only for deterministic timing arithmetic and reads the maintained solver call
sites and recorded dimensions.

## Two solver classes

### Reduced sizing oracle

`reduced_river_sizing_oracle.solve_reduced_river_sizing` compiles the exact
one-bet river security LP and invokes `maximize_linear_program`, the rejected
native simplex implementation. This is the class exercised by ADR-0311 through
ADR-0316. The corrected finite audit gives HiGHS dual simplex permission to
enter a prospective adapter gate; it does not connect HiGHS to this consumer.

The immediate sizing question is numerical authority, not whether Pontius can
outperform HiGHS. A separately named v2 adapter must propose a canonical
solution with HiGHS and accept it only after independent semantic
reconstruction and certification. No fallback to the rejected native solver
is allowed. Adapter rejection returns no sizing value.

### Behavioral one-seat master

`behavioral_one_seat_master` and its v2 successor already rebuild and solve a
SciPy `linprog(method="highs-ds")` model on every call. The retained wide
masters have 1,024 policy variables, six epigraph variables, 512 simplex
equalities, and six to nine coupling/cut inequalities. The retained
current-decision masters have 64 policy variables, six epigraph variables, 32
simplex equalities, and six to eight coupling/cut inequalities. Recorded HiGHS
iteration counts range from 3 to 23.

That product-of-simplexes shape plausibly admits persistent warm models or a
low-dimensional dual proposer. It is a different future optimization project.
ADR-0284 also establishes that the historical v1 feasible primal was mislabeled
as a mathematical lower bound. Any prospective master comparison must consume
`behavioral_one_seat_master_v2` or a later certified successor; historical
`U - L` labels cannot become replacement evidence.

## Perfect-solver upper bound

The two retained artifacts already expose every charged live component and
every master call. Summing their exact stored fields gives:

| Retained workload | Targets | Master solves | Master ms | Measured live ms | Perfect-solver ceiling |
|---|---:|---:|---:|---:|---:|
| wide Latin-E replication | 6 | 11 | `63.655000005383044` | `42,227.54269998113` | `0.1507428468%` |
| decision-aligned post-call shadow | 6 | 8 | `16.90849997976329` | `26,905.751100025373` | `0.0628434416%` |

Removing the fixed one-second-per-target emission reserve raises those ceilings
only to approximately `0.176%` and `0.081%` of measured non-emission work. A
solver with zero construction, solve, verification, and fallback cost cannot
save more than those shares on these panels. A one-to-two-order-of-magnitude
master speedup would therefore not materially move the present complete-ledger
quality-per-millisecond frontier.

By contrast, initial rows plus the first and retreat exact oracles consume
`27,593.948999987333 ms`, or `65.35%`, of the wide ledger and
`16,377.905400047893 ms`, or `60.87%`, of the current-decision ledger. This
does not prove that those components are reducible. It does prove that the
current master solver is not the binding measured component. ADR-0210 already
falsified call packing as a contraction reduction, and ADR-0218 classified the
maximum-width resident sparse path as compute pressured. Neither rejected
mechanism is revived here.

## Behavioral-master park and reopen rule

Do not implement a persistent private-HiGHS lifecycle, a custom dual
decomposition solver, or another native master while the complete-ledger
perfect-solver ceiling remains below `5%` on a prospectively frozen certified
v2 workload. Reopen the persistent public-HiGHS null hypothesis only after a
fresh complete ledger reaches at least `5%` aggregate master share or a frozen
per-target materiality rule identifies the master as the binding path.

If reopened, test persistent modify-in-place HiGHS and valid warm-basis reuse
before a specialized proposer. Differential every warm result against a cold
v2 rebuild and independent certificate. A specialized proposer remains
untrusted, with certified acceptance and HiGHS fallback. Its undetected
semantic-failure count must be zero; construction, update, verification,
rejection, and fallback time all remain charged. The project is not trying to
replace HiGHS as a general solver.

## Prospective reduced-sizing adapter contract

Authorize source implementation only after this ADR is committed. The new
module must not edit `linear_program`, `reduced_river_sizing_oracle`, any
hash-pinned audit source, or a v1-v4 owner. It must:

1. consume only the canonical `ReducedRiverSizingLinearProgram` and preserve
   its original row and variable units, trusted box, and objective offset;
2. invoke the public SciPy HiGHS dual-simplex interface with prospectively
   frozen presolve, primal/dual feasibility tolerances, and iteration ceiling;
3. reject every exception, nonoptimal status, nonfinite or wrong-width result,
   missing multiplier, and changed compiled identity;
4. reconstruct policy-simplex and chip-envelope feasibility separately in
   original coordinates under distinct nominal allowances;
5. clip only within a separately typed nonnegativity allowance, normalize each
   policy row exactly, and recompute the feasible behavioral security value
   and responder actions independently of returned envelope variables;
6. treat that feasible behavioral value as a maximization lower bound and
   derive an outward-rounded upper bound from independently bounded variables
   and normalized dual hints;
7. accept only a nonnegative certified `upper - lower` interval within a
   separately typed chip-valued width; and
8. retain raw status, iterations, objective, residuals, sign clips, rounding
   correction, certified endpoints, and timings as diagnostics without making
   them strategy quality.

The source boundary may use fake backends and bounded toy games only. It must
freeze its source/import closure, public runtime identities, options, semantic
allowances, result schema, and a later candidate-independent invocation
schedule before opening any sealed adapter result.

The later result gate should exercise the canonical 177 ADR-0312 bases rather
than all five numerical representations, because the production adapter
accepts only the canonical compiler output. Exact micro optima, exact
behavioral sizing reconstruction, and outward bounds remain authorities. A
complete pass may authorize a separately named v2 sizing-oracle integration
and wholly fresh future action mechanism; it may not revive v4 or reinterpret
its provisional A prefix.

## Dissent and kill criteria

The behavioral shape is unusually favorable to specialization, and a future
cut-rich or multi-round resolver can make master time grow. Parking it now is
therefore a scheduling decision, not a claim that specialization can never
win. The cheapest falsifier is a later certified complete ledger, not a raw LP
microbenchmark.

Kill the sizing adapter on any nonfinite accepted field, original-unit
violation, exact behavioral reconstruction mismatch, negative certified
interval beyond its distinct reversal allowance, certified width above its
frozen ceiling, source/environment drift, missing observation, or changed v1
consumer. A systems pass does not authorize a candidate-quality claim.

## Decision

Correct ADR-0316's active direction by separating the solver classes. Prioritize
one canonical, certified HiGHS dual-simplex adapter for the reduced sizing LP.
Park behavioral-master persistence and specialization under the `5%`
perfect-solver materiality trigger, and redirect current optimization attention
to exact row/oracle work under ADR-0283 through ADR-0285's v2 trust controls.

Commit this ADR and front-door correction before adapter source. Open no
sealed corpus, fresh sizing value, candidate mechanism, behavioral-master
result, or policy at this boundary. ADR-0281 remains revoked and v1-v4 remain
parked.

## Claims boundary

The ledger arithmetic is a deterministic re-expression of two retained finite
panels, not a new latency population or guarantee. The structural census covers
the recorded behavioral masters and maintained call sites, not every future
master. The sizing audit is finite spot-checking, not HiGHS certification.

This decision establishes priority and a prospective adapter contract only. It
does not establish a production adapter, persistent model, warm basis,
specialized solver, speedup, 15-second deployment fit, marginal decision
quality, action abstraction, blueprint, resolver, full-hand agent, AIVAT,
league strength, coalition safety, or poker strength.
