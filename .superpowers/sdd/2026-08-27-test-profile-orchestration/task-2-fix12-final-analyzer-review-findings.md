# Task 2 fix round 12 — final analyzer review findings

## Frozen identity and verdict

- Generator SHA-256: `416f95a02f8e8240aea3e775ed01369f3d97f6f1a09d23a12dfbf00f5af87c5a`.
- Narrow round-11 patch: 119,078 bytes, SHA-256
  `02738111975e2129224393c2651364e00537b0931c9316d2da438a1d5998c245`.
- Cumulative round-11 patch: 897,514 bytes, SHA-256
  `2549dcee61a1df18558b9f8ae73f073e287768df1a91f3d0f55f6a51f7b8ae70`.
- Both independent frozen reviews returned **OPEN**, with no Critical findings
  and the six Important groups below. Round 11 is rejected; CodeRabbit and
  integration remain prohibited.
- The complete tests-only union has SHA-256
  `64ec4868f6146042d8ff534949d72506043f01f4c948de1c8f2c386fbfa8a347`.
  The public real-runtime selector runs one test with 54 intended assertion
  failures and zero errors against the unchanged generator.

## Binding correction groups

### 1. Preserve implicit direct-`BaseException` residuals

Untyped `Call`, `Await`, `Yield`, and `YieldFrom` exits may be
`KeyboardInterrupt`, `SystemExit`, or `GeneratorExit`. Only bare and proven
`BaseException` handlers consume them definitely. `Exception` must retain
handled and direct-`BaseException` residual branches unless the state has an
exact `Exception`-subclass tag. The residual must survive suppress and finally.

### 2. Make bindings exact at each throw point

Carry separate normal and exceptional continuations. Commit assignment,
annotated assignment, named-expression, with-target, definition-name, and
augmented-assignment stores only after preceding evaluation succeeds.
Augmented assignment evaluates its target before its RHS. Model
`UNBOUND`/bound/maybe-bound distinctly across zero-iteration loops,
nonmatching match paths, and comprehensions. Comprehension targets do not leak.

Process tuple/list `del` targets recursively from left to right, retaining only
effects completed before a later target throws. Bind an `except ... as name`
alias to the caught exception instance, then delete it on every normal, return,
raise, break, and continue exit before finally; never restore an older binding.

### 3. Preserve exception-instance identity

Use one proven builtin-exception-instance flow value in both engines.
Successful assignment from a proven constructor retains it. It is valid as a
raise cause and invalid as a handler target. Handler aliases use the same
identity.

### 4. Respect source ordering and no-normal exits

Evaluate later call arguments, tuple elements, and raise causes only from the
preceding expression's normal continuation. Honor literal `and`, `or`, and
`IfExp` selection. A no-normal summary is allowed only for a local synchronous
non-generator `FunctionDef`, with no yield, whose every reachable exit raises
a proven builtin exception. Never apply it to arbitrary, async, or generator
calls. Feed its exact exception tag through handler and finally routing.

### 5. Separate generator construction from consumption

Generator-expression construction evaluates only its outermost iterable and
stores pending target/body/walrus effects. A directly resolved `next(g)` may
perform one bounded modeled iteration and commit effects only on its normal
continuation. Keep `Yield`/`YieldFrom` exceptional events in both engines,
including iteration failure without a syntactic call. Do not generalize the
generator protocol.

### 6. Keep safety and exception metadata closed and truthful

Do not prove set/dict displays or comprehensions nonthrowing without proving
hashing, mapping validation, iteration, target unpacking, condition truth, and
result insertion. Preserve safe recursive list/tuple cases. Complete builtin
exception spellings/ancestry, including `UnicodeDecodeError`,
`ZeroDivisionError`, `NotImplementedError`, and `SyntaxError`, but keep
constructor safety in a separate per-class shape table. Exception ancestry is
not proof that a constructor call cannot throw.

## Acceptance rule and Stage-C rim

A helper double or state-shape test never discharges a flow/ownership contract.
Each group requires a real CPython failure schedule, independent preclassifier,
resolver, and full census/resolver reconciliation, plus adjacent controls.
After GREEN: run all Task-2 gates, freeze new narrow/cumulative packages, obtain
two clean frozen reviews, and only then run CodeRabbit with untracked files.

This is not a general Python exception analyzer. Arbitrary operator overloads,
descriptors/subscripts, comparisons, f-strings, starred unpacking, dynamic
returns, cross-scope effects, imports, and general generator consumption remain
outside scope and conservative. The accepted boundary is exact source-ordered
normal/exception flow at declared call/await/yield, raise/cause/handler,
binding/delete, definition, with-target, and one direct-`next` seam.

## Post-acceptance architecture follow-up

Do not restructure mid-review. After acceptance, extract transaction/publication
and raw Git access from `tools/generate_test_inventory.py` into the typed shared
library, then separate discovery/inventory and AST analysis behind typed
interfaces. Otherwise `tools/` inherits the flat-source concentration problem.
