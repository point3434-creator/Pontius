# Task 2 fix-13 immediate tuple-generator review findings

## Frozen identity and verdict

- rejected generator SHA-256:
  `7fc84e76febb0a14e237f21473ba2bd7ab84afdf94270e7e9117cbf78369731f`
- corrected pre-existing layout tests baseline SHA-256:
  `6102c048a86e8f068cc0c3bd8303323115f9697bf29d8d4bfd246da000ec8822`
- 258-contract tests-only RED candidate SHA-256:
  `343323119350b1f17523cf64343da46a7c8e3554e821aa606ecacd898fe802fe`

After the census and layout corrections, working discovery reached its exact
capability-row oracle and produced 128 rows instead of 139. An exact comparison
found eleven missing and zero added rows. Every missing row is a fixture-scoped
`CuPy*AutomatonCache.compile` capability with `maximum_calls=6`, arising from
ten source sites inside an immediately materialized
`tuple(<generator expression over range(6)>)`.

## Root mechanism

Runtime discovery and `_runtime_call_bounds` already visit the generator body
and compute the correct bound of six. The independent preclassifier evaluates
only the outer iterable when creating a generator expression. The source-
ordered resolver similarly returns a deferred generator state. It consumes that
state only for direct `next`; `list` is deliberately blocked, and `tuple` has
no consumption branch. The inner call therefore receives neither a census
entry nor a resolver snapshot, and full review misclassifies the already-
bounded site as proved unreachable.

## Binding supported rim

Support only an immediate call to the unshadowed bare built-in `tuple` with
exactly one direct positional `ast.GeneratorExp`, no keyword or starred
argument, existing finite/supported single-generator provenance, and no
`NamedExpr`. Evaluate the callee and generator outer iterable before consuming
the body. Reuse bounded generator consumption for the exact finite cardinality,
including zero, exception closure, state transitions, and budget accounting.
Suppress generic unknown-call behavior only for this fully supported case.

Named, aliased, escaped, branch-merged, unknown-cardinality, walrus-bearing,
list-consumed, starred, invalid-shape, or shadowed-`tuple` cases remain on their
existing fail-closed or non-consuming paths. Do not broaden runtime bounds or
general generator semantics.

## Required RED evidence

The public selector adds twelve contracts:

1. finite `range(6)` materialization: runtime six, both analyzer axes identify
   the body call, one full-review row with `maximum_calls=6`, no blocker;
2. zero cardinality: no body execution, census, resolver call, row, or blocker;
3. exact deferred-consumption blockers for named, unknown-cardinality, walrus,
   direct and named `list`, `tuple` alias, and starred cases; and
4. rebound `tuple`, two-positional, and keyword forms proving that an
   unsupported callee/shape does not consume or classify the body.

The controller parsed both files and reproduced the selector under
`PYTHONHASHSEED=0` and `3`: 258 contracts, exactly six intended assertion
failures, zero errors, exit 1, and zero cache/bytecode artifacts. The failures
are the finite positive plus the five new fail-closed boundaries that the
rejected generator currently misclassifies; all six inverse/non-consuming
controls pass.

Production remains frozen until both exact-hash test-oracle reviews are CLEAN.
Only the preclassifier/resolver immediate-consumption path may then change.
Tests, native transaction/publication/Git code, configuration/model, H32,
generated governance files, CodeRabbit, commit, and integration remain frozen.

## Tests-only review acceptance

Both exact-hash reviews returned CLEAN with no Critical, Important, or Minor
finding. The primary reviewer returned TEST-SPEC and TEST-QUALITY CLEAN; the
independent mutation-oriented reviewer returned ORACLE CLEAN. Both reproduced
258 contracts and the same six intended assertion failures with zero errors
under seeds 0 and 3. Cardinality, zero-body suppression, exact bare-builtin
identity, direct/named list exclusion, alias/rebinding, invalid shapes,
blocker locations, and runtime/analyzer independence are accepted.

The tests are frozen and the bounded preclassifier/resolver correction is now
authorized under the supported rim above.
