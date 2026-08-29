# Task 2 fix 14 — deferred generator consumption provenance

Date: 2026-08-28  
Worktree: `D:/Pontius-worktrees/orch-task2`  
Branch: `codex/orch-task2`  
Base: `a2659766319900793d835c9abac8bb0f3cf173ba`

## Invalidated candidate

- Generator SHA-256: `794c3ed53e85fe2f5d5679665242f3643d4bab588a389cf01e9810f252120684`
- Test SHA-256: `dcb9ac0cebe56f1c66cb12feee2edde22b3623ad8d31b7ddd247ca01e016e53c`

The candidate correctly moved unsupported-generator sensitivity from generator creation to consumption time, but supported `next()` and direct finite builtin-`tuple()` consumption discarded protected provenance carried by the already-evaluated outer iterator.

Production-path reproducer:

```python
items = (cache.copy() for cache in (cp.arange(1),))
next(items)
```

CPython executes both `cp.arange(1)` and `cache.copy()`. The invalidated candidate derived exactly one eager `cupy.arange` capability row and no row or blocker for `cache.copy()`.

Both independent analyzers had the same omission:

- `_SensitivePreclassifier` did not retain outer-iterator sensitivity in `_DeferredGeneratorState` and bound the first target as insensitive during supported `next()` and direct `tuple()` consumption.
- `_SourceOrderedResolver` retained `outer_iterator_sensitive` but bound the first target to an insensitive unknown during `_consume_generator_expression()`.

Because both census and resolver lost the same provenance, reconciliation could not detect the false negative.

## Tests-only RED

The existing real `_review()`/`derive_design_review()` contract matrix was extended with runtime companions for:

1. sensitive outer result consumed by `next()` and used as `cache.copy()`;
2. the same flow through direct finite builtin `tuple()`;
3. a protected namespace yielded by the outer iterator and invoked through the generator target;
4. an inverse control where the sensitive outer target is never read by the delayed body.

Against the invalidated generator, the focused selector produced exactly three assertion failures, zero errors, and one passing inverse control. All three failures were missing blockers for the runtime protected target calls.

## Bounded correction

The correction is limited to outer-iterator provenance propagation:

- retain the preclassifier's eager outer-iterator sensitivity in `_DeferredGeneratorState`;
- bind the first generator target with that sensitivity in preclassifier supported `next()` and direct finite `tuple()` execution;
- bind the resolver's first target with `state.outer_iterator_sensitive` during supported consumption;
- use the established `mixed protected receiver is dynamically unresolved` blocker taxonomy for an unresolved sensitive yielded target.

No authorization, Git, transaction, publication, configuration, H32, generated inventory, or profile logic changed.

## Corrected frozen candidate

- Generator SHA-256: `108413e89fcc01b5bbc3f46b5bade66520e5535cde563960f4185222a8dc493e`
- Test SHA-256: `686e2abe0d3cd37bfa793cdec1eb660dcdf1480dbef9f7d0e9cc565ffc1c5a02`

Fresh evidence on these bytes:

- focused source-order/branch/generator matrix: pass at `PYTHONHASHSEED=0` and `3`;
- disposable D:-local inventory snapshot: 87/87 pass;
- working design derivation: 139 exact rows, 95 explicit blockers;
- capability digest unchanged: `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`;
- exact deferred blockers unchanged at four production sites;
- synthetic string-decoy census: 311 total, partitioned 17 design production / 6 historical production / 26 prior stabilization synthetic / 262 Task-2 synthetic, digest `e614ced09afb1b3e31ee0b8fc5098cf2dc0ea5b277087219fbbe74dd5f31f074`;
- default, `--write`, and `--check` all exit 0 and preserve governed output hashes;
- inventory SHA-256 remains `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
- profiles SHA-256 remains `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`;
- AST, canonical LF/no-BOM, generated format, zero-capability, cache, and transaction-artifact hygiene checks pass.

Independent clean verdicts and the final CodeRabbit uncommitted/untracked review remain required before Task 2 can be called complete. No commit, merge, push, or integration is authorized by this record.
