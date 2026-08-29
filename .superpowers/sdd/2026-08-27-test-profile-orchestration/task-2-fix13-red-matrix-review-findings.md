# Task 2 fix 13 RED-matrix review findings

## Reviewed identity and verdict

- generator SHA-256, stable at both review boundaries:
  `07e65029beee64706c339449c3687b8a36d118ae1fabf5c4364080119fe3b5b4`
- tests SHA-256, stable at both review boundaries:
  `2c67d6fe1e33a56e39b1d3505490ddb4e8bf66783f5438a8391efc1cff49bdca`
- binding production-findings brief SHA-256:
  `2c8ce572772a6ed50ce60457aeb1ab6e720bae8c628f9b179c0a4853a292dd93`

The tests-only candidate added 53 schedules/contracts, for 157 total, and
produced 32 assertion failures with zero unittest errors against the rejected
generator. Both independent test reviews returned OPEN with no Critical
findings. Production GREEN is not authorized until the matrix corrections
below are complete and independently reproduced.

## Binding test corrections

### 1. Separate the runtime callable from the analyzer source

The runtime oracle may execute `scenario(cp)`, but the direct preclassifier and
resolver must analyze the generated `review_source` function in which `cp` is a
real imported module. Do not force `aliases["cp"] = "cupy"` for a function
parameter. A correct lexical-entry implementation must treat parameters as
bound unknown and would otherwise be rejected by the test itself.

### 2. Observe rows, blockers, and errors simultaneously

A full-review observation is a tuple of matching protected rows, blocker
reasons, and any review exception. A blocker contract requires zero rows,
exactly the expected blocker, and no review error. A row contract requires the
exact row count, zero blockers, and no review error. A reconciliation-error
contract must not pass merely because the expected text appears alongside an
erroneous row or blocker. Apply this rule to generator, environment-poison, and
dynamic-reconciliation cases.

### 3. Complete and discriminate helper-call semantics

Add table-driven schedules for positional-only, positional-or-keyword,
defaults, required keyword-only, `*args`, `**kwargs`, duplicate values,
unsupported starred operands, valid keywords, and missing arguments. Include
same-tag every-exit, early normal exit, and different-tag exit helpers. The
same-tag schedule must prove there is no normal successor by placing a
protected call after the helper call inside the `try`; a generic may-raise
summary must fail that schedule. Preserve helper definitions by identity and
scope instead of a name-keyed dictionary that lets a nested same-name function
replace a module helper.

### 4. Complete lexical binders and both maybe-bound branches

Add module-helper masking schedules for `del`, import aliases, with targets,
match captures, class definitions, and nonlocal/present-absent controls in
addition to the existing assignment, annotation, loop, handler, and local-def
cases. Test both the normal and `NameError` branches of a maybe-bound read, and
both the successful and exceptional branches of maybe-bound deletion.

### 5. Prove exact reraised identity

For both bare `raise` and `raise alias`, retain the correct-handler schedule and
add an inverse observer in a wrong handler. Treating the reraise as generic
unknown must fail the inverse.

### 6. Prove constructor and invalid-raise exclusivity

Keep the positive `TypeError`/`OverflowError` handlers and add impossible-
handler inverses for invalid Decode/Encode/Translate shapes, Decode overflow,
and `raise 1`. Use a decimal integer literal beyond `Py_ssize_t` rather than an
attribute/arithmetic expression. An unknown or additional exception-instance
successor must fail.

### 7. Observe generator state, not only a downstream protected call

Count body/filter attempts. Abrupt body/filter failure must be observed exactly
once; a second `next` after close must not replay the exception. Follow invalid
`next` arity with a valid `next` and require one body execution. Add a real
runtime shared-alias/exhaustion count beside the review `maximum_calls` check.
Add a supported single-clause, known-positive, statically-true-filter control.
All blocker expectations must also require zero protected rows.

### 8. Pair optional comprehension paths

For unknown cardinality, require both the empty zero-iteration continuation and
a nonempty execution path. For an unknown outer filter, require both the false
skip path and the true path that reaches the later inner exception/body. A
correction that always keeps only the skip state must fail.

### 9. Prove decorator evaluation and application order

Add two decorators with independently recorded expression/application events.
Python evaluates decorator expressions top-to-bottom and applies decorators
bottom-to-top; an inner application failure prevents outer application and
definition binding. Retain the single-decorator throwing control.

### 10. Add real-runtime companions for environment and reconciliation

Groups 12 and 13 in the production brief need isolated CPython runtime
companions. Use a fake subprocess callable and a dynamic target observer; do
not launch an external process. Pair those runtime observations with the exact
row/blocker/error tuple from group 2.

## Retained strengths

The existing dict-unpack ordering, while re-test, refutable-match residual,
single-decorator application, runtime count encoding, and zero-error RED
mechanism are useful. The current 49 sampled runtime branches all matched their
claimed CPython counts. Preserve them while correcting the matrix.

## RED gate

Only `tests/test_inventory_and_profiles.py` may change. The generator must
remain exactly `07e650...b5b4`. The corrected public selector must finish with
only intended assertion failures and zero errors; every required family above
must contain a mutation-sensitive RED and a meaningful adjacent control. Parse
with `ast.parse` under `python -B`. Do not modify production, generated files,
configuration/model/H32, evidence, or native code; do not run CodeRabbit,
commit, or integrate.
