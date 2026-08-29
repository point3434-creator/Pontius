# Task 2 fix-13 final RED-matrix review findings

## Reviewed identity and verdict

- generator SHA-256, stable at every review boundary:
  `07e65029beee64706c339449c3687b8a36d118ae1fabf5c4364080119fe3b5b4`
- tests SHA-256, stable at every review boundary:
  `5a2b4ee5826d55b71eef4cd81022ccf3c6803789ce427ec623d74478028eab67`
- binding prior brief SHA-256:
  `6cd5d8024f3df26a2e2ba050d1586be865304e5ed518f60355079c73578b430b`

The controller reproduced one focused test with 61 assertion failures, zero
errors, exit 1, and successful parsing. Both exact-hash reviews returned OPEN
with no Critical findings. A targeted read-only adjudication also identified
one false RED and both reviewers agreed on its corrected disposition.
Production GREEN remains unauthorized until the finite union below is closed.

## Binding last test corrections

### 1. Prove static helper-call validity is exclusive

The positive handler rows do not reject a call-shape classifier that returns
generic unknown for every invalid shape. Add wrong-handler inverses for the
statically invalid literal shapes: positional-only by keyword, missing required
positional, missing required keyword-only, duplicate value, unexpected
keyword, and excess positional. None may retain the helper body's `KeyError`
successor after exact pre-call `TypeError`.

Add representative valid ordinary positional, keyword, defaulted, and
keyword-only inverses proving those calls do not retain an impossible
`TypeError` successor. Dynamic `*runtime_args()` and
`**runtime_kwargs()` calls remain deliberately nonexclusive because their
runtime shapes are not statically known.

### 2. Exclude a bound definition after decorator failure

Retain the positive `UnboundLocalError` observer, and add its inverse: after a
decorator application raises, read the function name; the protected observer
in the successful/bound branch must be unreachable. An analyzer that commits
the name before application and keeps both bound and unbound successors must
fail this case.

### 3. Prove invalid `next` calls raise before consumption

For zero-argument, keyword-argument, and three-positional-argument `next`, add
an analyzer-visible schedule in which consuming the generator changes a
receiver from `cp` to `safe` before the exact `TypeError` handler calls
`receiver.arange`. Correct pre-consumption validation leaves the receiver
sensitive in that handler; an ignored or consuming-invalid implementation does
not. Follow with a valid consumption and retain the real CPython count.

Add a wrong-handler inverse for each invalid shape so generic/unknown exception
routing cannot pass. Observe full-review rows, blockers, and errors together.
Do not rely on aggregate call counts that are identical when the invalid call
consumes and the later valid call merely sees exhaustion.

### 4. Make the second and third two-item transitions state-visible

Retain the exact `maximum_calls == 2` metadata control, but add source-flow
oracles. Reset an exception/receiver binding between the first and second
`next`; the generator body must update it again, proving the second body
transition occurred. Reset it after the second call and perform a third call;
the third call must not update it, proving exhaustion does not replay. A model
that derives the literal maximum correctly but marks the generator exhausted
after one modeled consumption must fail.

### 5. Correct the unknown-cardinality full-review false RED

For `[cp.arange(1) for _ in runtime_items()]`, the empty and nonempty runtime
companions legitimately differ only in their CPython counts. The analyzer sees
the same statically unbounded source. Both preclassifier and resolver must be
`sensitive`, proving the possible body successor is retained, but full review
must produce zero rows, the sole blocker
`dynamic repetition prevents a finite call bound`, and no error. Requiring a
finite row would invent an unsupported `maximum_calls` value and contradict
the established dynamic-repetition policy at generator lines 14843-14870 and
the retained unbounded-repetition tests.

## Preserve closed properties

Do not regress mixed-tag conservatism, dynamic star/kwstar handling,
`finally: return`, nonlocal helper identity and absent boundness, decorator
expression/application order, abrupt body/filter closure, comprehension skip
and execution successors, two-item maximum metadata, lexical/maybe-bound and
reraising controls, constructor exclusivity, dict/while/match ordering,
environment poison, reconciliation, runtime companions, simultaneous
row/blocker/error observation, or invocation of every prior regression group.

## RED gate

Only `tests/test_inventory_and_profiles.py` may change. The generator must
remain exactly `07e650...b5b4`. The public selector must parse and complete
with intended assertion failures only and zero unittest errors. Each new
negative must be mutation-sensitive against the frozen generator or an
explicit adjacent green policy control. Do not edit production, generated
files, configuration/model/H32, evidence, or native code; do not run
CodeRabbit, commit, or integrate.
