# Task 2 fix-13 corrected RED-matrix rereview findings

## Reviewed identity and verdict

- generator SHA-256, stable at both review boundaries:
  `07e65029beee64706c339449c3687b8a36d118ae1fabf5c4364080119fe3b5b4`
- tests SHA-256, stable at both review boundaries:
  `79e9c5220b4f4b3b9807b406f30ece19146e41d56a864b652421655eb7b96a47`
- production-findings brief SHA-256:
  `2c8ce572772a6ed50ce60457aeb1ab6e720bae8c628f9b179c0a4853a292dd93`
- first test-correction brief SHA-256:
  `9cbe5391a359e894d46d20be3991d54f230c8364d795eea53da738638710b13c`

The controller independently reproduced one focused test with 52 intended
assertion failures, zero errors, exit 1, and successful parsing. Both read-only
reviews returned OPEN with no Critical findings. Production GREEN remains
unauthorized. The remaining test corrections are the finite union below.

## Binding final test corrections

### 1. Keep different-tag helpers conservative and finish call-shape coverage

A helper whose reachable exits raise different proven tags is outside the
single-tag must-raise summary. Retain runtime zero for the existing mixed-tag
case, but require the preclassifier, resolver, and full review to keep the
post-call protected observer. Add an unrelated-handler inverse so an
unauthorized exact-tag or exact-tag-set summary fails.

Add a valid ordinary positional call, paired dynamic
`**runtime_kwargs()` valid/invalid shapes, an unexpected-keyword call, and an
excess-positional call. Add a `finally: return` helper control that overrides a
raise. Preserve the same-tag every-exit no-normal-successor RED.

Add present and absent nonlocal helper controls. A same-name module must-raise
helper must not replace an enclosing normal helper selected by `nonlocal`; a
conditionally absent enclosing binding must retain the `NameError` successor.
These must exercise helper identity and boundness, not only exception-name
provenance.

### 2. Make decorator order and failed binding visible to the analyzer

The runtime event log is necessary but insufficient. Add analyzer schedules
whose outcomes distinguish the order:

- outer decorator expression raises `KeyError`, inner expression raises
  `ValueError`: only the outer-expression tag is reachable;
- outer decorator application raises `KeyError`, inner application raises
  `ValueError`: expressions evaluate top-to-bottom but the inner application
  runs first, so only `ValueError` is reachable;
- after decorator application failure, reading the definition name takes the
  unbound-local path because the name was never committed.

For expression and application ordering, include both correct-handler and
wrong-handler observers. Every full-review assertion must inspect rows,
blockers, and errors together.

### 3. Observe abrupt generator closure in analyzer state

For both body and filter failure, the second `next` after the first exception
must observe a closed generator. Add a wrong-`KeyError` observer around the
second `next`; CPython produces zero protected calls, and a resolver that
replays the first exception produces a protected row or reconciliation error.
Retain the runtime attempt counter, but do not use it as a substitute for this
production-path analyzer assertion.

### 4. Require the nonempty unknown-cardinality successor

The existing empty/nonempty runtime pair shares an analyzer source whose
protected observer is reachable from the skip state, so a skip-only analyzer
can pass. Add an inverse source with the protected call in the comprehension
body, such as `[cp.arange(1) for _ in runtime_items()]`, and pair empty and
nonempty CPython runs. The analyzer must retain the body successor for unknown
cardinality while the existing case continues to require the zero-iteration
successor.

### 5. Complete the bounded direct-`next` rim quantitatively

Add zero-argument and keyword-argument invalid `next` calls, each followed by a
valid consumption proving the invalid call did not consume or close the
generator. Retain the three-argument case. Add a two-item generator that is
consumed twice, has one shared row with `maximum_calls == 2`, and does not
replay on a third call. These controls must reject an implementation that
accepts keywords/zero arguments or marks every generator exhausted after one
item.

### 6. Preserve all already-corrected oracle properties

Do not regress imported-module analyzer source, identity/scope-safe helper
collection, simultaneous row/blocker/error observation, lexical binder and
maybe-bound branches, reraise inverses, constructor exclusivity, dict-unpack
order, optional-filter successors, while re-test, refutable match, exact
environment poison, reconciliation, fake-boundary runtime companions, or the
invocation of all prior regression groups.

## Final RED gate

Only `tests/test_inventory_and_profiles.py` may change. The generator must
remain exactly `07e650...b5b4`. The public selector must parse and finish with
only intended assertion failures and zero unittest errors against that frozen
generator. Each correction above needs a mutation-sensitive analyzer result
and a real CPython companion where applicable. Do not edit production,
generated files, configuration/model/H32, evidence, or native code; do not run
CodeRabbit, commit, or integrate.
