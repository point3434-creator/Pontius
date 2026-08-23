# ADR-0311: Preregister the native-simplex robustness audit

- Status: accepted prospective candidate-independent solver audit before corpus source, corpus construction, audit-runner source, or any new LP result
- Date: 2026-08-23
- Follows: ADR-0310
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0311
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement only the value-free semantic reduced-sizing LP compiler and the two frozen audit-corpus constructors below, prove exact legacy-formula identity, unit tags, deterministic construction, diversity, and finite-inventory disjointness, then commit their source hashes and complete corpus identities before writing the audit runner or opening any native, HiGHS, enumeration, certificate, or objective result; do not modify the native simplex or reopen v4
- Front-Door-Blockers: neither prospective corpus exists; the reduced-sizing LP has no pure unit-tagged compiler; no audit runner or candidate-independent result exists; the native solver remains rejected for this workload; no replacement backend is eligible; v1-v4 and every action-abstraction integration path remain parked

## Question

Can the project replace an empirically brittle native two-phase tableau with a
backend whose outputs are independently bounded and invariant to exact LP
representations, without fitting a repair to ADR-0310's one known failure or
weakening any numerical or semantic-unit contract?

## Post-outcome disclosure and fixed boundary

ADR-0310 already reveals one development regression: the native solver fails
primal verification on the full-integer arm of
`adr0305-v4-qualified-b-c21`. Its returned tableau point violates one original
constraint by `4.049601922810204` chips against a
`4.199999999999999e-8` generic verification allowance. A diagnostic SciPy
HiGHS invocation finds a feasible point, but that post-outcome observation is
not replacement evidence.

This ADR uses the known LP only as a required regression. It freezes two new
prospective corpus streams, exact metamorphic transformations, independent
checks, backend options, and conjunctive gates before their source or values.
The audit is candidate-independent: it may not import an action abstraction,
evaluate v3 or v4, or infer action quality. ADR-0305 remains exhausted and v4
cannot be revived by any outcome here.

Freeze baseline commit
`f8936aca9d147e70f870148dff3548c09b13b983` and these immutable dependency
identities:

- native `linear_program.py`:
  `6069dac31bb2915284319d0d5551d5773f4b4cac294d07c440f4b4d9ee4c83f8`;
- reduced sizing oracle:
  `29b1d8fe9b73386200127cd30d5ceeaad0afff2d77ce6745b49e24d2db815697`;
- outward LP certificate:
  `0ca8b0443eb8a0279247fad659694d88b723b15bf0b2d3e5f7c7ef2c2ddfa910`;
- ADR-0309 structural source:
  `222f8ea8cfd3c7766440aebfc83010686c57d71da523819e9068e9d817d73bf5`.

The audit must not edit `linear_program.py`. A successor may extract the
existing reduced-sizing matrix construction into a pure compiler, but must
prove exact coefficient, bound, objective, variable-order, row-order, and
solve-path identity against an independent reproduction before any new corpus
value. The compiler must tag policy-simplex rows as dimensionless and
responder-envelope rows as chip-valued; a generic maximum residual cannot
stand in for either semantic check.

## Decision

Proceed only to value-free compiler and corpus construction under the frozen
mechanics below. Commit their exact source and corpus identities before
writing the audit runner or opening any new native, HiGHS, exact-enumeration,
objective, or certificate result. Keep the native solver unchanged, keep v4
permanently parked, and treat every backend as ineligible until the complete
conjunctive audit says otherwise.

## Frozen value-free corpora

Commit this ADR before implementing either generator. Both constructors use
ADR-0309's exact SHA-256 counter-word, unbiased `randbelow`, and Fisher-Yates
semantics through an independently differential-tested value-free source.

### Exact micro-LP corpus

Freeze seed text:

```text
pontius:adr-0311:native-simplex-robustness:micro-lp:sha256-stream:v1
```

Construct exactly 48 bounded maximization inputs with two through five
variables. For each ordered record:

1. set `variable_count = 2 + (record_index % 4)`, giving twelve records at
   each width, then draw one integer feasible witness coordinate in `[0, 4]`
   per variable;
2. draw an integer upper bound one through five above that witness and include
   the exact row `x_i <= upper_i`;
3. draw an integer lower bound in `[0, witness_i]` and include
   `-x_i <= -lower_i`, retaining negative right-hand sides when the lower
   bound is positive;
4. add `variable_count + 3` rows with coefficients drawn from `[-5, 5]`,
   rejecting only an all-zero row before consuming its nonnegative integer
   slack in `[0, 5]`, and set its exact right-hand side to
   `row @ witness + slack`; and
5. draw an objective from `[-5, 5]`, rejecting only the all-zero vector.

All inputs are exact integers and `x >= 0` remains the solver's implicit lower
bound. The explicit upper rows make every program bounded; the constructed
witness makes every program feasible. Store inputs and trusted box bounds
only. Do not enumerate a vertex or open an optimum during construction.
Freeze generator version
`candidate-independent-native-simplex-micro-lp-structure-v1` and ordered ids
`adr0311-simplex-micro-c00` through `adr0311-simplex-micro-c47`.

At audit time, independently enumerate every combination of active original
rows and nonnegativity boundaries needed to define a square system, solve each
system with `fractions.Fraction` Gaussian elimination, retain exactly feasible
vertices, and take the exact maximum objective. Bind the full vertex count,
maximizer count, exact optimum fraction, and one lexicographically smallest
maximizing vertex. Degenerate or non-unique optima are valid and must not be
filtered after construction.

### Fresh reduced-sizing corpus

Freeze seed text:

```text
pontius:adr-0311:native-simplex-robustness:fresh-width-four:sha256-stream:v1
```

Construct exactly 64 candidate-free width-four contexts. Reuse ADR-0309's
exact card construction, positive 16-cell rational range weights, showdown
filter, and minimum bet two. Cards and weights consume only this new stream.
Assign chips independently of stream outcomes so the first 60 records cover
the complete frozen Cartesian grid:

```text
pot   = (6,8,10,12,14,16,20,24,30,40)[index % 10]
stack = (10,12,16,20,24,30)[(index // 10) % 6]
```

The last four records repeat the first four chip pairs with new cards and
weights. Require semantic uniqueness within the corpus and zero counterpart in
the maintained finite inventory through ADR-0310. A collision rejects the
entire construction; do not skip, reseed, or enlarge after inspecting it.
Freeze generator version
`candidate-independent-native-simplex-width-four-structure-v1` and ordered
ids `adr0311-simplex-width4-c00` through
`adr0311-simplex-width4-c63`. Record the exact raw card-candidate count.

Compile exactly two candidate-independent arms per context:

1. minimum/all-in `(2, stack)`; and
2. full integer `tuple(range(2, stack + 1))`.

This gives 128 fresh reduced-sizing base LPs. The known ADR-0310 failing arm is
one separate development base, and the micro corpus contributes 48, for 177
total base LPs. No representative, v3, v4, or later qualified-B value may be
used.

## Frozen metamorphic variants

Freeze transform version `exact-lp-metamorphic-variants-v1` and seed prefix:

```text
pontius:adr-0311:native-simplex-robustness:transform:sha256-stream:v1
```

Derive a stream from that prefix plus each base identity. Commit all variant
identities before results. Each base produces exactly five mathematically
equivalent LPs:

1. canonical input;
2. an exact Fisher-Yates row permutation;
3. an exact Fisher-Yates variable permutation, including objective and trusted
   box-bound coordinates;
4. a row permutation followed by positive binary row scaling, with each row
   multiplied in both coefficients and right-hand side by one independently
   drawn factor from `2^-8`, `2^-4`, `1`, `2^4`, and `2^8`; and
5. a redundancy variant that appends exact duplicates of the first
   `max(1, ceil(row_count / 8))` rows in a stream-derived row permutation plus
   the exact row `0 @ x <= 0`, then permutes the complete row set.

Binary scaling is exact in Float64 for the frozen integer/dyadic inputs and may
not change the mathematical feasible set or objective. Store forward and
inverse maps, row origins, scale exponents, unit tags, and canonical/variant
digests. The corpus therefore contains 885 backend instances.

## Frozen backends and options

Run every instance through all three arms in the fixed order below. An arm
failure is captured as a semantic observation and does not stop later
instances: complete coverage is prospectively required because the native
regression is already known. No failure can be waived by another instance or
backend.

1. **Native diagnostic:** the frozen dependency-free two-phase
   `maximize_linear_program`, tolerance `1e-11`, maximum 4,096 pivots. It is
   already ineligible for this workload; the audit characterizes rather than
   promotes it.
2. **Replacement candidate:** SciPy `linprog(method="highs-ds")`, presolve
   enabled, primal and dual feasibility tolerances `1e-10`, maximum 4,096
   iterations.
3. **Corroborating control:** SciPy `linprog(method="highs-ipm")`, presolve
   enabled, primal and dual feasibility tolerances `1e-10`, IPM optimality
   tolerance `1e-12`, maximum 4,096 iterations.

The source must bind Python, NumPy, SciPy, and embedded HiGHS versions plus all
options. The current optional environment is NumPy 2.5.2 and SciPy 1.18.0;
these are environment facts, not frozen performance claims. Dual simplex and
IPM share HiGHS code and are not called fully independent solvers. Exact micro
enumeration, original-matrix reconstruction, and outward-rounded bounds carry
the independent mathematical controls.

For both HiGHS arms, negate the maximization objective and pass only the
canonical or transformed `A_ub`, `b_ub`, and implicit nonnegative variable
bounds `[(0, None)]`; do not add an equality, upper bound, scaling, or presolve
hint not already frozen above. Map the minimized objective and dual sign back
explicitly in the result schema.

## Verification and semantic units

Every backend result must be mapped back to canonical coordinates and checked
against original untransformed data. Store status, exception, iterations,
primal vector, dual hints, reconstructed objective, raw residuals, semantic
residuals, certificate bounds, and exact work. Do not trust backend success or
its aggregated feasibility field.

Use distinct frozen nominal allowances:

- micro primal/dual/objective and variant comparison:
  `1e-9` dimensionless;
- policy nonnegativity and simplex mass:
  `1e-9` dimensionless;
- responder-envelope feasibility:
  `1e-9` chips;
- reconstructed sizing objective:
  `1e-9` chips;
- certified sizing optimality interval width:
  `1e-9` chips; and
- cross-backend and cross-variant sizing interval/value comparison:
  `1e-9` chips.

Each allowance requires its own nominal type. No generic tolerance may be
reused because the numbers happen to coincide.

For micro LPs, compare each returned objective with the exact rational vertex
optimum and use the stored finite box in the outward certificate. For reduced
sizing LPs, map policy coordinates back, clip only values inside the frozen
dimensionless allowance, renormalize each opener row with exact
`Fraction.from_float` arithmetic, and independently reconstruct a feasible
behavioral value against exact joint weights and responder best actions. This
is the primal lower bound.

The policy variables have trusted box `[0, 1]`. Each shifted envelope variable
has trusted box `[0, payoff_span]`: policy simplex mass bounds every fold term
by half-pot and every call term by half-pot plus stack, while the existing
maximum-stake shift is half-pot plus stack. Feed backend dual hints and these
boxes to the outward-rounded certificate for the negated maximization problem;
the negative certified lower bound is a sizing-value upper bound. Record the
raw hint and every sign clip. The certified upper minus independently feasible
lower is the only optimality gap.

## Conjunctive gate

The audit is valid only if the value-free structure and runner source were
separately hash-committed before their next phase, every exact identity binds,
and all 2,655 planned backend invocations are represented once.

Require the native arm to reproduce ADR-0310's exact failure family, base,
canonical variant, call configuration, exception class/message, and failing
original row before interpreting any broader native result. Record all other
native successes and failures, but the native backend remains rejected
regardless of count. Any native result reported as successful yet outside the
independent exact/certified interval is a critical solver defect, not a value
to average away.

`highs-ds` becomes eligible only for a separate replacement preregistration if
all of these hold conjunctively:

- all 885 DS and all 885 IPM instances return finite optimal results without a
  status, iteration, schema, or numerical failure;
- every micro result and all five variants agree with its exact optimum within
  the dimensionless allowance;
- every reduced-sizing DS and IPM result has original-coordinate semantic
  feasibility and a certified interval no wider than `1e-9` chips;
- for every base, all ten DS/IPM variant intervals share a nonempty common
  intersection after only the frozen chip allowance; and
- DS and IPM independently reconstructed objectives differ by at most their
  frozen unit-specific allowance on every corresponding instance.

One failure rejects replacement eligibility. Do not pool errors, average
variants, discard a hard case, tune presolve/options, or select IPM after a DS
failure. A clean pass authorizes only a new prospective adapter/replacement
ADR; it does not change `linear_program.py`, any consumer, or any past result.

## Commit and invocation order

1. Commit this preregistration before corpus or compiler source.
2. Implement the pure semantic compiler and both value-free constructors;
   commit source hashes, exact corpus/variant identities, candidate attempts,
   disjointness, and tests before any new solve or exact optimum.
3. Implement the owned audit runner and result schemas with mocked/frozen-toy
   tests; commit its source hash before invoking it on the sealed corpus.
4. Invoke the complete audit once and accept or reject the conjunctive gate.

Do not combine these boundaries. A rejected invocation must retain its exact
prefix and failure records; a schema omission may be repaired only with an
explicitly disclosed unchanged reproduction that opens no unplanned input.

## Kill criterion

Corpus/compiler/audit source before this ADR; changed seed, count, transform,
backend, option, unit, allowance, or gate; solver value before the appropriate
source-and-identity commit; semantic collision that is skipped or reseeded;
candidate or forbidden v4 import; native-simplex modification; missing
backend-instance observation; post-failure case deletion; raw backend success
without original-coordinate verification; generic-residual substitution;
certificate box not derived from the game/input; exact enumeration after
filtering on its optimum; DS/IPM disagreement; post-outcome option tuning; or
any attempt to revive v4 or integrate a backend rejects the checkpoint.

## Successor authority

A complete pass makes one separately preregistered certified HiGHS dual-
simplex adapter eligible. It does not authorize that source, a native fallback,
consumer migration, replay, blueprint, convex-master, resolver, or strategy
integration. A failure leaves all current consumers fail-closed and requires a
new prospective solver mechanism or a return to exact small games; it does not
authorize corpus repair or threshold relaxation.

## Claims boundary

This audit can establish only numerical robustness and bounded objective
agreement on one known regression, 48 exact synthetic LPs, and 128 fresh
reduced sizing LPs under five exact representations. It cannot certify all LPs,
prove HiGHS independent of its own methods, establish poker frequency or
action quality, validate production ranges, change a prior experiment, or show
runtime suitability. Solver wall times are offline diagnostics only and may
not be mixed with per-iteration, per-solve, real-game, chip-quality, NashConv,
or 15-second action claims. No revoked experiment, external publication, or
research-thesis change is authorized.

## Preregistration boundary verification

Before this ADR is committed, the repository-wide unit suite passes 1,198
tests with two skips in 303.226 seconds. The generated-status check and the
documentation-integrity tests also pass. No audit compiler, corpus, runner,
new LP invocation, exact optimum, or backend result exists at this boundary.
