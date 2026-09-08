# ADR-0312: Seal the native-simplex audit compiler and corpora

- Status: accepted value-free compiler, corpus, and exact-representation seal before audit-runner source or any new LP result
- Date: 2026-08-23
- Follows: ADR-0311
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0312
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement only the owned native/HiGHS/exact audit runner and typed result schemas, including exact micro enumeration, original-coordinate sizing reconstruction, outward certificate plumbing, complete failure capture, and mocked or frozen-toy tests; commit its source hash, environment identities, backend options, and expected 2,655-invocation schedule before invoking any sealed audit instance; do not modify the native simplex, change a sealed corpus or representation, open a fresh optimum or sizing value, or reopen v4
- Front-Door-Blockers: no audit runner or result schema exists; no exact micro optimum, native/HiGHS result, sizing reconstruction, certificate interval, or backend timing has been opened; the native solver remains rejected for this workload and no replacement backend is eligible; v1-v4 and every action-abstraction integration path remain parked

## Decision

Accept and seal ADR-0311's pure unit-tagged reduced-sizing compiler, exact
micro corpus, fresh width-four corpus, known-regression snapshot, 177 ordered
base LP identities, and 885 ordered exact-representation identities. The
structures reconstruct deterministically, the extracted compiler is bit-exact
to an independent reproduction of the pre-extraction formula, every mixed-unit
row and variable retains a semantic tag, and the fresh contexts have no
counterpart in the finite maintained inventory through ADR-0310.

This checkpoint invoked no native or HiGHS backend, enumerated no exact vertex,
opened no optimum or sizing security value, evaluated no candidate, and built
no audit runner. The native simplex source remains byte-frozen and ineligible.
Capacity-filling v4 remains permanently parked.

## Pure compiler and preserved solve path

The new `pontius.reduced_river_sizing_lp` module imports no backend. It emits
the exact objective, inequality coefficients, bounds, variable order, row
order, maximum-stake shift, and objective offset formerly constructed inline
by `solve_reduced_river_sizing`. Its source SHA-256 is
`3a3ed588e90b84cdbc8186829fc7dac57d9ec40603f29dd5ddc70549748bd346`.

The compiler gives each policy-simplex row the dimensionless unit and each
fold/call envelope row the chip unit. Policy variables are tagged as
dimensionless probabilities; shifted envelope variables are tagged in chips.
Its trusted box is `[0,1]` for policy coordinates and
`[0,pot + 2*stack]` for shifted envelopes. The objective is chip-valued and
stores the separate envelope-shift offset rather than treating a coincident
stack or payoff span as the same quantity.

An independent test reproduction copies the formula from baseline commit
`f8936aca9d147e70f870148dff3548c09b13b983` without importing the compiler.
It compares `float.hex()` for every objective coefficient, matrix coefficient,
and bound on both arms of all four maintained reduced controls and on all 129
sizing bases sealed here. A mock stops the live oracle at its backend boundary
and proves that the solver receives the compiled lists and unchanged
`1e-11`/4,096 call configuration. Existing reduced-oracle and frozen
qualification tests reproduce through the extracted path.

The resulting `reduced_river_sizing_oracle.py` source SHA-256 is
`3ea2dd0bff8b1ce2790138d466a1fcecb9c9e450ae4d73423215af71da8e3c84`.
This is a formula-preserving extraction, not a solver or result change. The
native `linear_program.py` remains exactly
`6069dac31bb2915284319d0d5551d5773f4b4cac294d07c440f4b4d9ee4c83f8`.

## Sealed value-free structures

The isolated `pontius.native_simplex_audit_structures` source SHA-256 is
`ea945d3ce76b38c893029884bcbda2280fc22ce66fdac30fdb09508929d39801`.
It imports only `evaluate_seven` from the exact river evaluator and reproduces
ADR-0293's SHA-256 counter words, unbiased `randbelow`, Fisher-Yates shuffle,
and ADR-0301/0309 showdown filter through maintained differentials.

| Structure | Accepted inputs | Raw attempts | SHA-256 |
|---|---:|---:|---|
| Exact micro LPs | 48 | 312 random-row vectors; 48 objective vectors | `4a6d0a021ead74aa37f9379dc15184a259c51a205033f1f405d84605af970e14` |
| Fresh width-four contexts | 64 | 300 card candidates | `4bfde2a9937ceec206a40aa6c78c97335799413e6e8ef7de0fca6feef16dfcdc` |

The micro corpus has exactly twelve inputs at each width two through five.
Every input contains only exact integers, its stored witness satisfies every
row, explicit upper rows make the nonnegative program bounded, lower rows may
retain negative right-hand sides, every random row and objective is nonzero,
and the trusted box contains only structural bounds. No vertex or optimum is
stored. The stream happened to reject no random-row or objective vector; that
is a sealed observation about input construction, not a solver result.

The first 60 fresh contexts cover the complete ten-pot by six-stack Cartesian
grid with pot varying fastest. Contexts 60--63 repeat the first four chip pairs
with fresh cards and weights. Every context has 21 distinct physical cards,
positive exact rational mass on all 16 joint deals summing to one, and a
showdown matrix with both signs and at least three distinct rows and columns.
All 64 showdown matrices are distinct. The two fixed arms are minimum/all-in
and the full integer interval, yielding 128 fresh sizing bases.

An adversarial mutation test caught one uncommitted identity defect before
this seal: the first micro uniqueness check included `case_id`, so a numerical
duplicate under a fresh label would not collide. The final source separates
the label-bearing record digest from a label-free semantic input digest and
uses the latter for uniqueness. No input, seed, attempt count, solver call, or
result was changed or opened by that correction.

## Finite disjointness

The maintained prior inventory contains 988 unique semantic contexts: the 748
contexts through ADR-0304 plus all 240 value-free ADR-0309 representative,
qualified-A, and qualified-B contexts. Context ids are excluded; cards, chips,
minimum bet, ordered hand axes, and every exact joint probability are included.

| Inventory | Contexts | Semantic-inventory SHA-256 |
|---|---:|---|
| Maintained through ADR-0310 | 988 | `8109c680918c689ca603a26cc19c846f3933cfd448f6c019da4755d08ae6155b` |
| ADR-0311 fresh width four | 64 | `2553bbc6023eaebdf296d83b5ee130755934b433af3138c5239c7e8f9f26cbb5` |

The exact intersection has size zero. The complete disjointness-evidence
SHA-256 is
`c5db1cecd1d31edc4847a9e9daec554ea90de165c4901384ee5bf4197809e653`.
This is an exhaustive absence claim over those finite inventories only; it is
not an IID, poker-frequency, or representativeness result.

## Known regression and complete corpus

The corpus owns a standalone exact snapshot of only ADR-0310's disclosed
qualified-B context 21 and its full integer arm. The structural context,
oracle context, structural-to-oracle binding, and stopped failure retain their
recorded hashes. A differential against the parked source proves every card,
chip, hand-axis, probability, and full-size field. The new regression-input
identity is
`4a08dde49bc006bf38b8b8b86763055570219aca3b520f56a9319a5c99ee35dc`.
The audit corpus source imports no v4 module.

The separate `pontius.native_simplex_audit_corpus` source SHA-256 is
`b65c301b9f0443b9f25da4da22fa7f8c15017cd63b4abe2670c5d98c32085918`.
It orders the known regression first, the 48 micro bases next, and the 128
fresh sizing bases last, with minimum/all-in before full integer for each fresh
context.

| Manifest | Records | SHA-256 |
|---|---:|---|
| Ordered base corpus | 177 | `8201b331a0bb936f1bd3e2dd78acf46278ff063d6b86cf045df7e56f2141019d` |
| Ordered representation corpus | 885 | `5c024f281afe348578018ffa321edd7b276316a3da27f163e1f50cd7f3eb76fe` |
| Complete value-free corpus | 177 bases / 885 variants | `4be6dcc311bc2f885ce9ad312cee8294f38231180ab78bbbfb6497184b1597a3` |

For each base, the transform stream seed is the exact ADR-0311 prefix, a
literal colon, and the base-record SHA-256. The five ordered representations
are canonical, row permutation, variable permutation, permuted dyadic row
scaling, and redundancy. Each descriptor stores both variable-map directions,
both row-map directions (one-to-many for duplicates), row origins and roles,
scale exponents, row and variable units, the base hash, and a hash of the
fully materialized numeric LP. Materialization checks every one of the 885
hashes without invoking a backend. The redundancy descriptor contains exactly
`max(1, ceil(rows/8))` duplicates and one dimensionless zero row.

## Verification

Focused compiler/oracle tests, structure/corpus tests, source-isolation tests,
the frozen ADR-0310 qualification preservation test, and the documentation
gates pass as a 49-test focused slice in 50.783 seconds. They cover exact legacy
matrices, the live solve seam, semantic units and boxes, both streams, all
structural invariants, raw attempts, deterministic identities, complete finite
disjointness, known-regression binding, all representation-map directions,
dyadic scaling, redundancy, source imports, native-source immutability,
malformed fields, label-only collision adversaries, and frozen dataclass
mutation. The repository-wide suite passes 1,215 tests in 330.826 seconds with
two intentional environment-dependent skips. Ruff lint/format, generated
STATUS, maintained Markdown links, and whitespace checks pass.

## Next boundary

Implement the owned audit runner and typed result schemas separately. That
source may implement the exact rational micro enumerator, original-coordinate
sizing reconstruction, outward certificate adapter, the three frozen backend
adapters, exception-complete observation records, and the 2,655-call schedule.
It must pass only mocks and frozen toy inputs, then commit its source hash,
runtime identities, backend options, and schedule before the first invocation
on any sealed base or variant. It may not change a corpus identity, edit the
native simplex, tune an option, call one real audit instance, or inspect an
optimum during that source checkpoint.

## Claims boundary

This result establishes deterministic value-free inputs, exact compiler
identity over the tested finite formulas, semantic unit propagation, exact
representation identities, and finite-inventory disjointness. It does not
certify either solver, open a candidate-independent quality result, establish
an optimum, show runtime suitability, validate production ranges, revive v4,
or improve a poker decision. It establishes no latency, marginal decision
quality per millisecond, 15-second feasibility, replay, blueprint,
convex-master, resolver, NashConv, AIVAT, league-strength, C5-completion, or
complete-bot result. No revoked experiment, external publication, or thesis
change is authorized.
