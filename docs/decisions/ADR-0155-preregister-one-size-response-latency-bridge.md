# ADR-0155: Preregister the one-size response-latency bridge

## Status

Preregistered after ADR-0154 and before any fresh-panel response-bridge rerun.
No h32 strategy-quality or online-deployment claim is authorized by this ADR.

## Context

ADR-0154 established that exact clean-fringe fixed-policy utility is not an
exact unilateral-gain certificate for opponent seats. The next bounded question
is therefore operational: can the already accepted resident response verifier
close a source-relative envelope certificate after one retained one-size warm
step inside a 15-second decision boundary?

The answer must distinguish an exact-target cache that is already resident from
one that must be constructed after the decision state arrives. Conflating those
clocks would make the deployment conclusion uninterpretable. Action emission is
not yet instrumented, so no reserve value can be promoted to a measured tail.

## Frozen workload

The executable contract is
`experiments/configs/h32-response-latency-bridge-v1.json`. It pins:

- all twelve ADR-0148 fresh-panel targets in their original order;
- only the already labeled one-size `search_current1` candidate;
- the original immutable source-average64 blueprint and target belief;
- the fixed label-free seat order `0,1,2,3,4,5`;
- one resident warm step and one exact early-stopping response verification;
- the 15,000 ms hard decision boundary; and
- unmeasured emission-reserve sensitivity rows at 0, 250, 500, and 1,000 ms.

There are no new strategy-quality profiles. Exact prefix evaluations are
compared with the retained complete teacher vectors from ADR-0148. GPU policy
digests are disclosed but not required to match across runs; utility,
best-response, and deviation-gain coordinates must reproduce within `1e-9`,
and the verifier stop reason and stop seat must match exactly.

## Clock decomposition

Each target records three nested clocks before the unmeasured emission reserve:

1. `prepared`: one warm search step, exact response certificate, and selection;
2. `target_cache_resident`: solver construction and blueprint warm start plus
   the prepared clock; and
3. `cold_target`: target belief-workspace construction, GPU incidence
   construction, all six resident response caches, and the target-cache-resident
   clock.

Source public topology construction is outside all three clocks because the
online architecture requires it to remain resident. The prepared clock has the
stronger explicit precondition that the exact target workspace, GPU incidence,
six-seat caches, and warm solver state already exist.

Deadline counts are descriptive outcomes, not gates. The integrity gates cover
frozen identities, teacher reproduction, exact stopping, fail-closed blueprint
fallback, finite telemetry, bounded resource use, and a clean run. This prevents
an observed timing result from changing whether its own measurement is accepted.

## Decision rule

Accept the latency measurement only if every outcome-neutral gate passes. For
every incomplete certificate, select the immutable blueprint. Do not treat an
unfinished certificate as partial value, extend the deadline, reorder seats,
change the candidate, or reanchor after seeing timing.

Even if a preregistered sensitivity row fits 15 seconds, keep
`deployment_authorized=false`. A later runtime audit must measure state-ingest,
synchronization, and action-emission tail latency and set the actual fallback
cutoff. No p95 or p99 population claim is permitted from twelve heterogeneous
one-shot targets; the conservative observed maximum is reported instead.

## Consequences

If the prepared clock fits but the cold-target clock does not, residency and
incremental target-state maintenance become architectural requirements. If the
prepared clock itself does not fit, the next work is an incremental response
bridge or a smaller deterministic search budget, not a larger atomic autopsy.

No two-size tree is constructed. Strategy quality remains frozen and claim-null.
