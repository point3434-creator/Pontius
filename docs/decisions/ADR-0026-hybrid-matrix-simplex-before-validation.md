# ADR-0026: Use a verified hybrid matrix simplex before validation

**Status:** Accepted after a failed validation-generation attempt; no scheduler
verdict was produced

**Date:** 2026-08-19

## Incident

The first run of the committed validation configuration stopped before writing
an artifact. The exact normal-form teacher for
`river-g000204-correlated` exceeded the specialized packing simplex's
100,000-pivot cap. No scheduler holdout was invoked, no aggregate or fold result
was computed, and test remained unconstructed.

The failing normal form has 81 row plans and 256 column plans, of which 81
payoff columns are unique. The packing tableau numerically cycles despite its
deterministic pivot order. The existing independently verified two-phase linear
program solves the identical packing formulation in 31 pivots, with zero
matrix duality gap and behavioral NashConv `3.11e-15`.

A wholesale backend replacement is not robust: on
`river-g000181-correlated`, the two-phase tableau alone exceeds its strict
primal-feasibility tolerance while the packing solver returns a verified
solution in 53 pivots.

## Decision

Use a hybrid matrix-game oracle. Attempt the small specialized packing tableau
first. Track visited bases and abandon it on a repeated basis or after a bounded
fast-path pivot budget. On that numerical stall only, solve the same shifted
packing LP with the two-phase simplex. Regardless of backend, retain all
existing primal/dual value checks and the river oracle's independent behavioral
NashConv check.

Record `simplex_backend` and `simplex_pivots` in every new river teacher label.
This makes fallback use auditable rather than silent. The change affects only
the offline exact teacher; it does not alter DCFR traversal, online features,
the frozen scheduler, budgets, splits, or gates.

## Pre-rerun audit

Before rerunning the unchanged validation configuration, solve all 296
validation teachers without constructing scheduler traces. All pass: 295 use
the packing backend and one uses the two-phase fallback. Maximum reported
backend pivots are 104. Maximum matrix duality gap and behavioral NashConv are
both `8.6534e-11`.

This teacher-only audit necessarily identifies the numerical failure but does
not inspect DCFR features, checkpoint strategies, fold allocations, or the
scheduler verdict. Commit the hybrid oracle before rerunning validation.

## Dissent protocol

**Confidence:** high that the two observed numerical pathologies are covered;
moderate that no other generated matrix family exposes a third tableau issue.

**Opposing evidence:** both backends use floating-point simplex arithmetic, and
the fallback is no longer independent of the shared general LP implementation.

**Mitigation:** every returned matrix strategy is verified against the original
unreduced payoff matrix and then converted to behavior and checked by dynamic
best response. Any verification failure still aborts the dataset.
