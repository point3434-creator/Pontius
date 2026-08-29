# Task 2 fix-13 production GREEN rereview findings

## Frozen candidate identity and verdict

- generator SHA-256, stable at every diagnostic boundary:
  `f581c3c29b156fab7b4e52737fb323b744a482cff913ffadde82953e6313d0e2`
- accepted 240-contract tests SHA-256:
  `92b8ae99757077208aecad24652f1438e0989c589d9bcfd3a4f943eecffaf1b6`
- corrected 246-contract tests-only RED candidate SHA-256:
  `5f396043fbb4779ea8fd293042abb2c552849061c8e60ba477e4327841905a70`
- binding fix-13 production brief SHA-256:
  `2c8ce572772a6ed50ce60457aeb1ab6e720bae8c628f9b179c0a4853a292dd93`

The focused public selector passed all 240 accepted contracts with zero
failures or errors. The prescribed full suite then ran 87 tests in 71.770
seconds and failed with one failure and three errors. The default CLI exit-2
failure is derivative of the three reconciliation errors below. Two fresh
exact-hash read-only diagnostics returned OPEN with no Critical finding. The
candidate is rejected; production is frozen.

Both exact-hash tests-only rereviews of the corrected 246-contract candidate
returned CLEAN: primary TEST-SPEC and TEST-QUALITY, and independent adversarial
ORACLE, with no Critical, Important, or Minor finding. They reproduced only
intended assertion failures, zero errors, successful parsing, the expected
warning, and zero cache artifacts. The tests are accepted and one bounded
generator-only correction is authorized under the groups below.

## Binding correction groups

### 1. Preserve inherited sensitivity through attribute receivers

`_SensitivePreclassifier._expression(ast.Attribute)` currently evaluates its
base to `(qualified, sensitive)`, but when `qualified` is non-null returns only
the result of `_qualified_call_is_sensitive(supplied)`. A receiver represented
as an unknown synthetic qualified name plus `sensitive=True` therefore loses
the inherited taint.

This one mechanism causes both resolver-only census failures:

- `backend = backends[1]; backend.arange(1)` in the focused container fixture;
- `numerators = cp.arange(...).reshape(...); numerators.copy()` at
  `tests/test_resident_record_to_hand_fold_v2.py:312` in the real corpus.

Preserve inherited base sensitivity in the attribute result, conservatively
combining it with exact qualified-call sensitivity. Retain the deliberate safe
observation exemptions at the call boundary. Do not special-case containers or
`.copy()`.

### 2. Never overwrite a more precise source-ordered helper return

`_review_body` correctly computes the local-alias helper return
`runner -> subprocess.run` with `_source_ordered_helper_return`. During
`_SourceOrderedResolver` construction, `_trivial_helper_return` then replaces
that exact result with the weaker bare qname `launch`. The outer call loses its
subprocess provenance while the independent census retains it.

Preserve caller-supplied exact helper returns, for example with `setdefault`,
instead of overwriting them. A trivial fallback may fill only a genuinely
missing summary. The existing direct-return, local-alias-return, and
divergent-return tests remain the controlling RED and inverse cases.

### 3. Key nested returned callables by definition point, not bare name

Two different factories may each define and return a nested callable named
`decorator`. The preclassifier globally copies nested summaries by bare name;
the direct resolver similarly flattens nested definitions; and the full
resolver can overwrite its correct factory-specific source-ordered result with
the same trivial bare-name fallback. Factory traversal also derives partly
from a set, making the wrong selected tag process-order dependent.

For an outer factory whose nested decorator raises `KeyError` and an inner
factory whose same-named nested decorator raises `ValueError`, CPython applies
the inner decorator first. Only the `ValueError` observer is reachable. Carry
a factory/definition-point-qualified returned-callable marker and associate
its callable summary with that marker. Remove global nested-name flattening.
Resolve missing external-factory returns through source-ordered analysis.
Ambiguous, conditional, unsupported, or reassigned definitions remain unknown;
they must not be guessed by name.

## Required RED evidence and scope

The existing full/focused suite already supplies strong RED coverage for the
container and local-alias helper-return mechanisms. Add only:

1. positive `ValueError` and wrong-handler `KeyError` same-name nested
   decorator pairs in both factory-definition orders, observed through runtime,
   preclassifier, direct resolver, and full review, so neither first-wins nor
   last-wins bare-name selection can pass; and
2. `x = cp.arange(1); x.copy()` plus a safe/nonprotected receiver counterpart,
   proving inherited receiver sensitivity rather than a container-only patch;
   the full-review blocker is bound to `tests/test_review.py:7`, not merely its
   item and reason.

The controller reproduced the amended public selector against the frozen
rejected generator: 246 contracts, only intended assertion failures, zero
errors, exit 1, successful parsing, the expected CPython 3.14 warning, and zero
cache artifacts. A ten-process seed matrix exposed the rejected candidate's
unordered bare-name traversal: `PYTHONHASHSEED` 0, 1, 2, 5, and 8 produced
three failures, while 3, 4, 6, 7, and 9 produced five. The invariant failures
are the original decorator pair and receiver reconciliation; affected seeds
also fail the reversed-definition-order pair. The safe receiver always passes.
After independent test-oracle review, one bounded correction may
modify only `tools/generate_test_inventory.py`. Native transaction,
publication, Git, configuration/model, H32, generated governance files,
CodeRabbit, commit, and integration remain outside this correction.

## Acceptance gates after correction

The exact amended public selector and all 87 inventory/profile tests must pass
with the explicit `PONTIUS_GIT` executable. The real corpus and synthetic
container/helper tests must reconcile, the default read-only CLI must return
zero, both Python files must parse, and cache/capability artifact censuses must
remain zero. The corrected exact bytes then require two fresh direct reviews
before CodeRabbit may run.
