# ADR-0318: Source-seal the certified reduced-sizing HiGHS adapter

- Status: accepted source-only canonical adapter and toy controls before any sealed validation base
- Date: 2026-08-23
- Implements: ADR-0317
- Preregistration commit: `ea48fea`
- Adapter: `src/pontius/certified_reduced_sizing_highs.py`
- Adapter canonical-LF SHA-256: `4723a7b153b6285081c67e8e5c20b0f1097c7d8acf9ab4c5482373984947e80f`
- Seal canonical-LF SHA-256: `25acaef5776044b56ad370d42616200cc39d3d662a7ab1bc45f3366a6ae1c0b0`
- Control canonical-LF SHA-256: `a4639e9cc39c801924a0de74cb3c5c695865d1f1e75169a1fc0ffb2d575ffae7`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0318
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement and source-seal only a failure-complete canonical 177-base validation runner over ADR-0312's exact ordered bases: verify the ADR-0318 source/dependency/runtime seal before the first call, invoke one public HiGHS-DS proposal per canonical base, independently recheck exact micro optima or exact behavioral sizing lower bounds and outward upper bounds, retain every typed success or exception in order, and freeze the complete schedule/result schema before any sealed invocation; edit no adapter, v1 consumer, corpus, candidate owner, or allowance and open no v1-v4 value
- Front-Door-Blockers: the certified adapter has run only analytic and bounded toy controls; no source-sealed 177-base validation runner or adapter-specific retained result exists; no production v2 sizing-oracle consumer is authorized; v1-v4 remain parked; behavioral-master specialization remains below its materiality trigger

## Question

Can the reduced-sizing HiGHS dual-simplex adapter be implemented as an
untrusted proposer behind independent semantic authority without touching the
rejected native consumer or opening a new corpus value?

This is a source-only checkpoint. The adapter and its controls were implemented
after ADR-0317 was committed at `ea48fea`. No ADR-0312 base, ADR-0310 context,
fresh action panel, candidate value, or strategy label was invoked.

## Canonical adapter

`solve_certified_reduced_sizing_highs` accepts exact pot, stack, minimum bet,
joint `Fraction` probabilities, showdown signs, and exact increasing bet sizes.
It recompiles those inputs through the pure `reduced_river_sizing_lp` compiler,
then submits only that canonical matrix to the public SciPy
`linprog(method="highs-ds")` interface.

The frozen backend options are:

| Option | Value |
|---|---:|
| method | `highs-ds` |
| presolve | `true` |
| primal feasibility tolerance | `1e-10` |
| dual feasibility tolerance | `1e-10` |
| maximum iterations | `4,096` |

Variable bounds are the compiler's finite trusted box: policy variables in
`[0,1]` and shifted chip-envelope variables in `[0,payoff_span]`. The adapter
uses no private persistent model, basis, native fallback, transformed
representation, or candidate-specific option.

## Independent acceptance authority

HiGHS supplies only raw primal coordinates, a reported minimization objective,
and inequality multiplier hints. The adapter rejects exceptions, nonoptimal or
malformed status, missing messages, wrong widths, nonfinite fields, missing
multipliers, and negative iteration counts before semantic acceptance.

Acceptance then requires all of the following in original coordinates:

1. policy lower/upper violations are within a distinct dimensionless
   nonnegativity allowance;
2. raw and post-clip row masses plus the compiler's dimensionless rows are
   within a distinct simplex-mass allowance;
3. shifted-envelope box and chip-row violations are within a distinct
   chip-valued envelope allowance;
4. the reported HiGHS objective agrees with a direct canonical dot product;
5. every tolerated policy clip is recorded, each row is converted from its
   literal Float64 values to exact `Fraction`, and each row is normalized
   exactly;
6. an exact behavioral fold-versus-call evaluation of that normalized policy
   supplies the feasible maximization lower bound and responder actions;
7. that lower bound agrees with the raw canonical objective under its own
   reconstruction allowance; and
8. `linear_program_certificate` treats the SciPy multipliers only as hints,
   clips wrong signs, minimizes every stationarity residual over the trusted
   box with outward rounding, and supplies a minimization lower bound whose
   negation is the sizing maximization upper bound.

The signed `upper - lower` interval has separate chip-valued reversal and
width allowances. Both are frozen at `1e-9`, as are the five other semantic
allowances. Seven equal numerical values remain seven nominal types; numerical
coincidence cannot cross-wire their gates. A tolerated negative reversal is
retained signed and reported as a zero nonnegative gap. A material reversal or
wide interval rejects the proposal.

The returned immutable schema retains exact and Float64 policies, exact
response actions, raw primal and multiplier vectors, clips, original-unit
residuals, reported/canonical/behavioral/certified objective fields, certificate
rounding and sign-clip diagnostics, solver status/iterations/message, and
separate solver and verification wall times. None is a strategy-quality label.

## Source and runtime seal

`certified_reduced_sizing_highs_seal` freezes the canonical-LF hashes of the
adapter and its two Pontius dependencies:

| Source | Canonical-LF SHA-256 |
|---|---|
| certified adapter | `4723a7b153b6285081c67e8e5c20b0f1097c7d8acf9ab4c5482373984947e80f` |
| bounded certificate | `0ca8b0443eb8a0279247fad659694d88b723b15bf0b2d3e5f7c7ef2c2ddfa910` |
| canonical sizing compiler | `3a3ed588e90b84cdbc8186829fc7dac57d9ec40603f29dd5ddc70549748bd346` |

The later sealed runner must call the source/dependency verifier and bind
CPython `3.14.6`, NumPy `2.5.2`, SciPy `1.18.0`, and embedded HiGHS `1.12.0`
before its first backend invocation. The solve itself remains on SciPy's public
interface; the embedded private module is read only to identify the bundled
HiGHS version.

The seal records the future canonical validation inventory as one known
regression, 48 exact micro bases, and 128 fresh sizing bases, 177 total. It does
not yet freeze base IDs or own an invocation. A separately source-sealed runner
must bind the exact ADR-0312 order and one complete observation per base before
opening any adapter-specific result.

## Toy-only validation

Eleven focused controls pass. They cover:

- one-type analytic always-win and always-lose games;
- a nontrivial canonical two-type game with an exact certified interval;
- a bounded two-by-two differential against the separately enumerated normal-
  form teacher;
- the exact public method, options, and finite trusted box;
- nonoptimal status, wrong primal width, NaN primal, false reported objective,
  missing multiplier, probability-bound corruption, and useless-dual
  mutations;
- a compiler rejection before backend entry and nominal allowance cross-use;
- immutable result-schema mutation; and
- the adapter import graph, unchanged legacy consumer, canonical-LF seal, and
  frozen runtime identities.

The bounded normal-form control is development evidence only. The adapter
source imports neither `linear_program` nor `reduced_river_sizing_oracle`;
the test imports the historical bounded teacher independently. No native
solver is a production fallback or adapter authority.

## Decision

Accept and source-seal the canonical adapter and toy controls. It is eligible
only for a separately source-sealed, failure-complete 177-base validation
runner. That runner must retain every scheduled observation after an individual
adapter rejection and use the exact micro/behavioral/certificate authorities
already frozen by ADR-0311 through ADR-0313.

Do not edit or connect `reduced_river_sizing_oracle`, invoke ADR-0310, revive
v4, construct a fresh action mechanism or panel, or call this source a
production replacement. The historical native failure and ADR-0314 rejection
remain part of the record.

## Claims boundary

This checkpoint establishes source structure and bounded toy behavior. It is
not evidence over the 177 canonical bases, arbitrary reduced games, numerical
conditions, or future SciPy/HiGHS versions. It does not establish a production
consumer, fallback frequency, latency distribution, speedup, sizing quality,
action abstraction, 15-second fit, marginal decision quality, blueprint,
resolver, full-hand agent, AIVAT, league strength, coalition safety, or poker
strength. Behavioral-master persistence and specialization remain parked.
