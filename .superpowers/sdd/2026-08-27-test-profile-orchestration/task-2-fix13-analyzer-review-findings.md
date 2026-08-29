# Task 2 fix 13 analyzer review findings

## Frozen candidate identity and verdicts

The reviewed candidate did not move during either review:

- `tools/generate_test_inventory.py` SHA-256:
  `07e65029beee64706c339449c3687b8a36d118ae1fabf5c4364080119fe3b5b4`
- `tests/test_inventory_and_profiles.py` SHA-256:
  `b95421b61972ff606f400d7b57a78db56de0a37f0a85e40244701deddba4af39`
- rejected round-11 generator baseline SHA-256:
  `416f95a02f8e8240aea3e775ed01369f3d97f6f1a09d23a12dfbf00f5af87c5a`

The primary frozen review returned SPEC OPEN and QUALITY OPEN. The independent
adversarial review returned OPEN. Neither review found a Critical or Minor
finding. Both verified that the baseline-to-candidate delta is confined to the
analyzer, `_review_body` reconciliation, and the two required analyzer-support
imports. No native transaction, Git, atomic-write, or publication definition
changed.

The focused round-12 selector passed all 104 schedules, but the prescribed full
suite, run with
`PONTIUS_GIT=C:/Program Files/Git/cmd/git.exe`, ran 87 tests and failed with four
failures and two errors. The full-suite regressions are part of this binding
correction set; focused GREEN alone is not acceptance evidence.

## Binding correction groups

### 1. One signature-aware helper summary at the executed definition point

`_BoundedCallableSummary`, `_bounded_call_shape`, the preclassifier, resolver,
and `_review_body` must use one definition-identity summary. The summary must
model positional-only, positional-or-keyword, defaulted, required keyword-only,
`*args`, `**kwargs`, duplicate, and unsupported-starred call shapes without
claiming an incorrect exact exception. A valid keyword call to
`def boom(x)` enters the body; omitting required `*, x` raises `TypeError`
before body entry. Decorated replacements are not the original helper unless
application is proven. Remove the legacy name-only `_bounded_local_raise_tag`
override in `_review_body`. A bounded synchronous helper whose every reachable
exit raises the same proven tag may be summarized; a helper with any normal or
different-tag exit may not be.

Primary locations: generator lines 8165, 8222, 10268, and 14339 in the rejected
candidate.

### 2. Complete lexical-local classification and truthful entry boundness

Before source-order execution, compute the function's complete lexical-local
set while honoring `global` and `nonlocal`. A later assignment, value-less
annotation, `del`, import, loop target, with target, handler alias, match
capture, or local definition makes the name local for the whole function and
must mask a same-name module alias/helper/assignment at entry. A declared
global is entry-bound only when the global is actually proven present. These
states must be explicit; bound-but-unknown must not collapse to unbound.

This closes the module-helper/local-`UnboundLocalError` omission and the real
corpus failure where a bound unknown `resident` is deleted before the later
CuPy call.

Primary locations: generator lines 8418, 8883, 9219, 10106, 10262, 10656,
10674, 11949, 13127, 13286, and 13310.

### 3. Maybe-bound names retain both normal and exceptional successors

Reading a maybe-bound sensitive callable must retain its sensitivity on the
normal successor and an exact `NameError` successor; it must not silently lose
the blocker. Deleting a maybe-bound name must fork to a successful deletion
state and an exact `NameError` state. Deleting a definitely bound but unknown
value must continue normally. Preclassifier and resolver must agree.

This closes the existing
`test_import_time_nested_and_duplicate_sensitive_calls_fail_closed` error and
the real-corpus independent-census mismatch at
`tests/test_legal_river_quotient_cuda_compensated_tiles.py:191`.

### 4. Handler aliases and reraising preserve exact or unknown identity

Bare `raise` inside a handler must preserve the active exact caught tag.
`raise error` where `error` is an exception instance with an unknown tag must
remain unknown and must never stringify `None` or index the built-in ancestry
table with it. Handler matching must be defensive for noncanonical tags.

Primary locations: generator lines 12230 and 12584.

### 5. Decorator application is an eager throwing source point

Evaluate decorator expressions in Python order, apply them after creating the
function object and before binding the definition name, and route application
exceptions. Do not commit the definition name on an application path that
throws. Preserve the ordinary decorated-replacement behavior required by group
1.

### 6. Exception construction and explicit raise use a three-way classifier

Replace the Boolean constructor-safety predicate with `valid`, `definitely
invalid`, or `unknown`. Cover the canonical literal shapes for
`UnicodeDecodeError`, `UnicodeEncodeError`, and `UnicodeTranslateError`, plus
ordinary safe constructors such as `NotImplementedError()`. Decode indices
must fit `Py_ssize_t`; overflow remains an `OverflowError` successor.
Definitely invalid constructors retain no normal exception-instance successor.
A definitely invalid raised value such as `raise 1` produces only exact
`TypeError`, not an unknown explicit exception.

Primary locations: generator lines 8128, 8607, 8651, 11262, 11303, 11463,
11554, and 12246.

### 7. Dict unpack validation is source ordered

Validate each `**` operand immediately before evaluating any later dict entry.
For `{**1, "x": cp.arange(1)}`, runtime raises `TypeError` before the CuPy
call. Do not delay unpack validation until after later keys and values, and do
not conflate unpack mapping validation with final key hashing.

### 8. Direct `next` stays on the bounded rim

The only fully modeled generator consumption is an exact one- or two-positional
argument `next` of a single-clause generator with a known positive remaining
cardinality and statically true filters. Unknown outer cardinality, dynamic
filters, nested clauses, divergent exhaustion state, and generator/non-
generator joins must not speculatively commit body or walrus effects; emit the
stable blocker `deferred generator consumption is dynamically unresolved`.
Invalid `next` arity raises before consumption. A filter/body exception closes
the generator so a later `next` cannot replay its effects or exception. Shared
aliases observe one state and exactly-once body execution.

Primary locations: generator lines 8179, 9420, 10473, 11106, 11474, 11489,
11678, 11703, 11766, and 11884.

### 9. Comprehension optional and exceptional successors are source ordered

Unknown cardinality retains a zero-iteration successor. An optional outer
filter's skip state survives a later inner iterator that raises. Target-unpack
mismatch throws before filters or body. Later clauses must not erase skips
already produced by earlier clauses. Preserve both preclassifier and resolver
dispositions without creating a general CFG.

Primary locations: generator lines 11696 and 11731.

### 10. Every bounded `while` re-test uses successor routing

The initial test and the one bounded re-test must use the same successor-aware
evaluation. If the body changes the condition callable to a must-raising helper,
the second test has no normal successor. Mirror the one-retest model in the
preclassifier.

Primary locations: generator lines 12408 and 12432.

### 11. Refutable match nonmatch is independent of guard evaluation

Preserve a refutable pattern's nonmatch input before evaluating the matched
path's guard. A guard that raises removes only the matched successor; it cannot
erase the nonmatch state that proceeds to later cases.

Primary locations: generator lines 12480 and 12489.

### 12. Exceptional environment poison remains exact across joins

The existing full-suite contract requires
`subprocess environment exceptional state is ambiguous` after divergent
environment branches flow through an exceptional successor. Do not overwrite
that poison with the generic `subprocess environment branch state is
ambiguous` during a later join. Restoring the exact poison also restores the
established dynamic-child wrapper reason.

### 13. Reconciliation remains fail closed without manufacturing reachability

The independent census and source resolver must reconcile every sensitive site
as a row, stable blocker, or proved-unreachable disposition. The correction may
not weaken the two reconciliation assertions merely to make the suite pass.
Repeated-call snapshot accumulation is already correct and must remain so.

## RED test contract before production changes

Expand the public round-4 selector with real CPython schedules for every group
above and adjacent controls. Each schedule must compare runtime behavior with
the independent preclassifier, source resolver, and full review/reconciliation
where applicable. An exception raised by the analyzer is an observed mismatch,
not a harness error. Tests must fail as assertions against the frozen
`07e650...b5b4` generator, and the combined selector must finish with zero test
errors.

The matrix must include at least:

- valid keyword, missing required keyword-only, decorated external/module,
  same-tag all-exit, and normal-exit helper controls;
- representative lexical binders plus present/absent `global` controls;
- bare and alias reraises, including unknown alias identity without a crash;
- decorator application failure;
- valid Encode/Decode/Translate and ordinary constructors, invalid shapes,
  Decode overflow, invalid raised value, and dict-unpack source order;
- unknown/dynamic/nested/divergent/merged generator states, invalid `next`
  arity, abrupt close, and supported exactly-once controls;
- comprehension zero-iteration, optional-filter/inner-raise, and target-unpack
  schedules;
- second-while-test and refutable-match-guard schedules;
- bound-unknown delete, maybe-bound delete, maybe-bound sensitive call, and the
  exact exceptional-environment reason.

Run the existing broad failing tests as part of RED evidence. Do not change
production, generated inventory/profile, configuration/model, H32, evidence,
or native transaction/publication files during the RED phase. Do not run
CodeRabbit, commit, or integrate.

## Explicit non-goals

- no general Python CFG or arbitrary generator-protocol analyzer;
- no scientific or GPU payload execution;
- no transaction, native I/O, Git, or publication refactor;
- no generated capability write or approval-token use;
- no commit, integration, or CodeRabbit run until a later exact candidate has
  passed broad verification and both direct reviews.
