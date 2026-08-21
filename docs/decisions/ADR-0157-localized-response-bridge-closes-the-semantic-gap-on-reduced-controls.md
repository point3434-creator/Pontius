# ADR-0157: The localized response bridge closes the semantic gap on reduced controls

## Status

Accepted as an additive exact semantic bridge after ADR-0156. It authorizes
engineering and preregistration of an h32 incremental-response implementation,
not an h32 timing run, strategy-quality claim, or deployment claim.

## Context

ADR-0154 proved that an exact clean-fringe fixed-utility delta can still miss a
best-response change, including at a blueprint-zero-reach information set.
ADR-0156 then showed that recomputing the accepted full resident response prefix
after one warm step is exact but exceeds the 15-second boundary on five of
twelve fully prepared targets even before action emission.

The missing semantic layer is a source-relative response certificate that
treats policy atoms as mutable inputs, propagates every affected selector, and
keeps deadline selection separate from scientific exactness.

## Engineering result

Add `src/pontius/local_response_bridge.py`, SHA-256
`29384af18b3fd122173b5099f78040a35b949597883f20954193ff5dca6d6b9f`,
and `tests/test_local_response_bridge.py`, SHA-256
`b8b54c7eb8c25dfeaa3738616c047dc1c407c233ba922d3c3c4a90bca9c6fa19`.

The bridge uses the existing `CompiledPolicyDeltaTape` as its reduced exact
reference. Every candidate is evaluated from immutable source values in a new
epoch. The bridge:

- binds the complete `DeltaCertificateScope`, blueprint policy digest,
  candidate policy digest, immutable gain vector, payoff span, and epoch;
- rejects an empty delta or a delta wider than the caller's frozen information-
  set atom limit;
- returns exact utilities, best-response values, deviation gains, and response
  actions;
- reconciles per-seat response-action switches with the tape's aggregate
  selector-flip count;
- classifies cap and objective conditions independently;
- simulates the accepted cap-before-objective fixed-seat prefix; and
- applies the 15-second deadline only in the subsequent fail-closed selection
  function, never by truncating or relaxing scientific exactness.

## Controls

Five direct controls pass.

1. Two distinct single-information-set candidates match independent complete
   evaluation and remain source-relative across call order and an identity read.
2. A zero-blueprint-reach atom leaves every fixed utility unchanged but changes
   best-response values and reports selector switches.
3. Manufactured cap and objective prefixes preserve cap precedence and the
   exact objective lower-bound stop.
4. Scope mutation, an invalid atom limit, and a deadline at the emission cutoff
   all fail closed to the blueprint.
5. A six-player h3 factor-belief case compares the sparse source-relative tape
   with the accepted leaf-adjoint reference. Utilities, best-response values,
   and deviation gains agree within `2e-14`; every best-response action agrees.

The complete suite passes 603 tests with 22 optional GPU screens skipped.

## Decision

Adopt the reduced semantic bridge as the oracle for the next implementation.
Do not claim that the flat dependency tape itself scales to h32 or that its
unpreregistered h3 execution time predicts GPU latency.

The next implementation should cache source terminal response numerators and
selector state per target seat, recompute only terminal contributions affected
by a localized opponent-policy delta, and replay the public reverse pass from
an immutable source epoch. A target player's own policy edit must reuse that
target's source best-response value exactly while still updating fixed utility.

Before any h32 replay, reduced controls must compare the new cache against both
the flat tape and the accepted leaf-adjoint evaluator for:

- one same-seat atom and one opponent-seat atom;
- zero reach;
- no selector switch and at least one selector switch;
- cap pass/fail and objective pass/fail outcomes;
- call-order and stale-epoch mutations; and
- complete-vector and fixed-prefix decisions.

Only after those controls pass may a frozen h32 preflight measure persistent
bytes, affected terminal work, response latency, conservative observed maximum,
and the 15-second ledger on already labeled policies. Strategy quality remains
claim-null.

## Dissent

**Confidence:** very high in the reduced bridge's exact semantics and scope
discipline; moderate that terminal-numerator caching is the best h32 physical
representation.

**Opposing evidence:** the clean-fringe fixed-utility path already supplies a
compact cutset representation. A response representation organized directly
around clean frontier nodes may beat terminal-level invalidation.

**Largest unknown:** whether late public atoms touch few enough target-omitted
terminal factors for the cached response path to beat the complete resident
seat evaluator at h32.

**Cheapest falsification:** implement the cache on the h3 control and count
affected terminal contractions separately for same-seat and opponent-seat
atoms before allocating any h32 GPU run.
