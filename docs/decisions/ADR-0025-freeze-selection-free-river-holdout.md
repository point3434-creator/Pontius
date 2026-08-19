# ADR-0025: Freeze the selection-free river holdout

**Status:** Accepted; frozen before validation construction

**Date:** 2026-08-19

## Decision

Use `river_scheduler_holdout` as the only evaluator for
`river-post-probe-scheduler-v1` on reserved sequential-river contexts. It
contains no candidate enumeration, training choice, threshold selection, or
fallback substitution. It applies the committed active-raw/shallow-12.5% rule
exactly once to each evaluation pool.

The production rule SHA-256 is
`74d6c3d68dbb7363af9927b72f83dce7769613656df8253ace36a1ff0cc598bd`.
The evaluator rejects another hash even if its rule ID and status are unchanged.
The validation and test trace configurations are also committed before either
is run; their SHA-256 digests are
`84f3f3fc4a17b709ee7b143c4fa3cddf4edd24ffa34b20111e333c6713eb3e1c`
and
`9fe063a699c18d6e10b2a6e3ce21dd8320d65a41d5090fd636ea2565a5ccccdb`.

## Evaluation semantics

Generate exactly one reserved split at a time from the frozen 400-group
universe. Use only DCFR and checkpoints 0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32,
48, and 64. The trace separately times a minimal one-pass active regret summary
at every checkpoint; the rule charges the checkpoint-two measurement. Exact LP
teachers, exploitability, and future checkpoint outcomes remain diagnostic and
cannot enter the score or allocation.

Hash each board group into one of five folds. Apply the same fixed rule
independently inside every fold, including rank construction and donor funding.
This makes each fold repay its own iteration and state-work budget. Aggregate
the five disjoint fold results for the primary verdict. A separate whole-split
application is diagnostic only.

The validation rule passes only if it:

1. strictly improves raw final exploitability in every fold;
2. captures at least 25% of aggregate exact post-probe perfect uplift;
3. exceeds neither fixed iterations nor fixed deterministic state visits in
   any fold; and
4. improves aggregate raw reduction per charged measured millisecond.

The evaluator reports the exact perfect allocator only after applying the fixed
rule. It is the denominator for the preregistered capture gate, not an online
dependency.

## Sealed test

Do not construct the test trace during validation. A test invocation must
supply a validation result whose status is
`validation_passed_test_authorized`, whose rule ID matches, and whose embedded
rule SHA-256 equals the current frozen artifact. Otherwise the evaluator stops
before reading outcomes. Test uses the identical rule and gates.

If validation fails any gate, retain fixed checkpoint-four DCFR, do not inspect
test, and do not retune this rule. A later experiment would require a new rule
version and a new untouched data source.

## Dissent protocol

**Confidence:** high that selection and rule mutation are mechanically blocked;
moderate that serial Python timing is stable in aggregate; low that a positive
river result would transfer to six-player play.

**Opposing evidence:** fold-local pools are research proxies for concurrent
speculative jobs, timing still combines recorded solver intervals with a small
separately timed summary, and only board/range transfer is tested.

**Largest unknown:** whether the 2.33% development rate edge survives new board
groups after all feature and decision costs.

**Cheapest falsification:** run validation once. Its result determines whether
test remains sealed.
