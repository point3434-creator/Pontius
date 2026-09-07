# Immutable blueprint preparation brief

Base: `363c9fb669e19a30375537ee5e92ea338a840a2d` (ADR-0512).
This is a Tier C source-opening design, not an implemented speedup.

## Purpose and acceptance

Prepare an owned immutable blueprint once per runtime hand, retain its unchanged
canonical digest, and use complete decision keys for repeated lookup. Provide the
same prepared lookup to direct Python research callers. Complete integration means
the real child runtime uses it in both blueprint selection and baseline fallback.

Accept only if the old artifact bytes, source digest, provider configuration,
actions, hit/miss labels, legality checks, visible-state limits and clock accounting
keep their meanings. Preparation belongs inside the existing hand-start accounting
boundary. The independent table host continues to calculate fallback with the
sealed reference implementation. Source checks keep their full identity contract.

Ground truth is the unchanged `immutable_blueprint.py`, artifact codec and host
validator, supplemented by literal legal-action/card/history controls authored
before GREEN execution. The reference comparison proves compatibility; independent
literal controls prevent a shared assumption from being the only action oracle.

The measured motivation is ADR-0512's fixed 1,024-entry probe: about 6-7 ms per
provider call, with 92.6% of profiled provider cumulative time in table digest work.
These are finite local observations. Measure cold construction, warm lookup and
memory separately; neither an unmeasured speed target nor an entry cap is a gate.

## Boundaries and scope

Seams: caller graph to owned prepared source; complete visible key to indexed
action; prepared source to runtime hand-start and action boundaries; child action
to independent host validation; raw committed source to each tool's admission;
old evaluator tests to their pinned historical snapshot; current tests to v3.

Add a two-file package, a versioned evaluator, finite tests and a fixed historical
test launcher. Only the exact old-path exceptions in `source-contract.md` may be
changed after a separately authorized source-opening adoption. The blueprint,
codec, provider rules, action ledger and v1/v2 evaluators remain sealed references.

Expected source size is roughly 250 new preparation lines, 150 integration and
admission lines, the approximately 624-line evaluator copy, and 150 historical
launcher lines. Expect 800-1,200 new test lines. These are planning estimates, not
invented execution or acceptance limits. The evaluator copy is required by sealed
history; the small fixed launcher preserves existing tests. Reassess the design
before building a generic framework or expanding the named file population.

## Dependencies, authority and stop rule

Only deployment of the prepared runtime and its new evaluation entry point waits
on this source round. Artifact authoring, earlier result interpretation and other
research planning do not depend on it. No source edit precedes opening adoption.

Use one initial design candidate and at most two bounded corrections; apply the
workflow's earlier stop for repeated residuals on one contract or WRONG SHAPE.
Source implementation has the same round budget. Two independent CLEAN Tier C
reviews precede final snapshot gates and exact decision commit authorization.
Unexpected source populations, new capability grants or changed clock semantics
require a revised design, never a weakened check.

This opens finite engineering correctness and cost controls only after adoption.
It opens no training, playing-strength inference, native engine migration, learned
blueprint, operating session or consumed experiment owner. The existing 14,000 ms
work cutoff and 15,000 ms action wall remain authoritative.
