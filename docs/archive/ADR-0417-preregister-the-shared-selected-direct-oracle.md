# ADR-0417: Preregister the shared selected direct oracle

- Status: accepted prospective exact-work boundary; the selected direct-query row is frozen as a read-only projection of the fully accumulated direct-fold coefficient vector, so one source-rank traversal must produce both query and fold outputs without reassociation, deleting 34,003,200 projection-only source unrankings and 27,783,168 redundant boundary pair additions while every parent source, consumed owner, numerical gate, resource ceiling, capacity rule, complete 25-card value, actual 45-card value, solve, action, 15-second result, decision-quality result, truncation choice, blueprint result, and poker-strength claim remains unchanged or unopened
- Date: 2026-08-26
- Follows: ADR-0416
- Config: `experiments/configs/legal-river-quotient-cuda-shared-direct-oracle-v1.json`
- Config canonical-LF SHA-256: `48ad381d36767bdce973c464fb3bfc0d925cac4e45a790129b50324098a9dab7`
- Retained outcome commit: `4d77dc39f5c1b2536bc7673ec57e96ecb92828a3`
- Immutable V4 artifact SHA-256: `4c038ffd45aa1b23e5e4aaf8cef4fbeafaf489a141e58335baf1b66e598816c6`
- Prospective source: absent
- Prospective controls: absent
- Prospective result: absent
- Reserved actual result: absent
- Real CUDA calls authorized here: `0`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0417
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement and source-seal only the additive shared selected direct oracle from the clean ADR-0417 preregistration: hash-bind the immutable V4 and paired sources; preserve `direct_selected_queries_tile` byte-for-byte as a future differential control; replace exactly the `direct_selected_fold_tile` span so its finished coefficient vector emits both boundary query pairs and the unchanged fold pairs; independently rederive the 10/22/25-geometry work deletion, pair-order proof, source builder closure, alias rejection, and mutation controls without importing CuPy or compiling, loading, launching, reading, or creating any result; keep every owner, reader, device value, capacity projection, population-25 fixture, action, quality, truncation, blueprint, and strength field absent
- Front-Door-Blockers: no source-sealed shared selected direct oracle or real byte-identity differential exists; the sole V4 path remains consumed with a conservative capacity rejection, and this boundary selects no replacement projection rule; no passing complete-25 capacity verdict, complete 25-card numerical result, actual owner, or full-width actual-context quotient value exists; no general odd-chip or side-pot leaf automaton, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Question

Does ADR-0416's dominant-phase ledger expose one exact common subexpression
that can be removed before redesigning any capacity estimator or touching
production adjoint machinery?

## Decision

Yes. Preregister one additive shared selected direct oracle and nothing else.
The config is the complete authority for parent identities, algebra, work
counts, future controls, source-seal restrictions, kill criteria, and claims.
It was frozen with source, controls, owner, reader, and both result paths
absent. This decision performs no CUDA work and reopens no V4 path.

### Exact identity

For selected query mask `q`, logical feature `f`, and source rows in
increasing colex rank, both current direct kernels compute

```text
C_f(q) = pair_fold in increasing r over X[r,f]
         for every source mask r disjoint from q
```

The current query kernel returns `C_f(q)` for the eight frozen boundary
features. The current fold kernel first computes the same `C_f(q)` for every
logical feature in the tile, then consumes that finished vector in increasing
global-feature order to form numerator and reach.

The two kernels therefore duplicate the source unrank, disjointness test, and
boundary-feature pair additions. Interleaving additions to different feature
accumulators does not alter any one accumulator's sequence. The successor
keeps one thread per selected query, the fold kernel's strict source-rank loop,
its strict logical-feature loop, and every pair primitive. Only after the
complete source loop may it copy the eight owned boundary slots to a separate
query output and then execute the unchanged fold loop. Copying the two Float64
components is not arithmetic.

This is stronger than a numerical equivalence claim: under the frozen loop
order, every shared query pair must be byte-identical to the unchanged
reference kernel. No epsilon, tolerance, reduction tree, atomic, warp
collective, feature-major source traversal, or reporting equivalence may decide
that identity.

### Exact work deletion

Across two families, two repeats, and three tiles, the shared path removes:

| Population | eliminated source unrankings | eliminated boundary pair additions | replacement pair copies |
|---|---:|---:|---:|
| complete 10 | 40,320 | 512 | 512 |
| complete 22 | 14,325,696 | 9,504,768 | 512 |
| projection-only 25 geometry | 34,003,200 | 27,783,168 | 512 |

All direct-fold source unrankings, 176-feature compatible coefficient
additions, query-weight construction, pair products, numerator/reach additions,
selected queries, boundary features, families, repeats, and tiles remain.
The source implementation and an independent control must rederive these
counts; the config cannot certify itself.

ADR-0416 measured `direct_query` at 1,942.753945 seconds of the frozen
projection and `direct_fold` at 2,640.480457 seconds. Selection uses those
facts only to choose the duplicate work. It does not reinterpret the rejected
projection. A reporting-only calculation says perfect deletion of the
22-endpoint query phase would have changed its nonauthoritative guarded total
from 196.213399834 to 159.935904814 seconds. That is a mechanism-size prior,
not a capacity result, because the V4 maximum-over-endpoints rule remains
rejected and consumed.

### Alternatives not combined here

Reusing forward source coefficients inside the adjoint contraction is
algebraically plausible: both kernels traverse the same 90 pairings in the
same order. It is not admitted here because it changes table lifetime,
forward/adjoint scheduling, and production memory residency. It deserves a
separate gate if still material after the shared direct result.

Fusing signed-target extraction with the adjoint contraction is not admitted.
It changes thread ownership and reduction structure, so pair order and
resource behavior would require a different numerical proof. No redundant
adjoint recurrence term was found in this call-graph spot check.

Changing projection endpoints, subtracting observed fixed overhead, dropping
the ten-card endpoint, widening a wall, or choosing truncation is measurement
or strategy design—not this exact-work mechanism. None is smuggled into the
source boundary.

### Source seal and later device authority

The additive source builder may replace exactly one CUDA span:
`direct_selected_fold_tile`. It must leave the parent
`direct_selected_queries_tile` bytes unchanged as the future device
differential authority. The population path may not launch that reference
kernel; a later separately preregistered bounded owner may invoke it only in a
typed complete-ten control.

Before any device result, the source seal must prove with a pure CPU sequence
model and static source inspection that boundary copies occur after the full
source traversal, query/fold/coefficient storage cannot alias, source and
feature orders are unchanged, work counters are exact, and early-copy,
boundary-shift, alias, source-reversal, dropped-low, swapped-pair, and
feature-major mutations reject. The source seal may not import CuPy, compile,
load, launch, create an owner or reader, or read/create the prospective result.

A later real differential requires a new preregistration and exclusive result.
It must compare the unchanged query kernel with shared query output byte for
byte on complete ten, retain fold identity, run existing numerical gates on
complete 10/22, and recheck executed-cubin/driver resources. This ADR selects
no future capacity endpoint or projection rule.

### Continuity

The generated-front-door historical labels remain literal. ADR-0328 precedes
the direct closed finite-block greedy line. ADR-0367 preregisters the occupied-
card quotient. ADR-0368 seals the exact bounded algebra keystone. ADR-0369
freezes the source-only arithmetic boundary. ADR-0370 seals the numeric-array
and logical-work result. ADR-0378 freezes the source-only literal-target
liveness boundary. ADR-0379 retains the 244,970,204-byte margin. ADR-0381
source-seals the one-shot literal-45 CUDA owner. ADR-0384 retains the passing
literal-45 result and opens the actual-context quotient bridge. ADR-0385
preregisters the actual-context quotient bridge. ADR-0386 records the source-
sealed actual-context quotient bridge. ADR-0387 freezes the consumer-capacity
seam. ADR-0388 records the source-sealed CuPy-free consumer-capacity answer.
ADR-0383's owner was invoke exactly once and remains consumed by ADR-0384.
ADR-0396 through ADR-0403 own and close the three work-preflight owners.
ADR-0404 through ADR-0406 own and close the exact-cubin diagnostic. ADR-0407
through ADR-0409 own and close the empty selector. ADR-0410/0411 freeze and
seal only the suffix diagnostic; ADR-0412 consumes its owner and retains its
result; ADR-0413 freezes V4; ADR-0414 corrects only its evidence envelope; and
ADR-0415 source-seals the composite successor without invocation; ADR-0416 consumes it and retains the frozen capacity rejection; ADR-0417 opens only the shared-direct-oracle source question. No earlier
owner is revived.

All 177 ordered observations pass under ADR-0320. The phrases exclusive
untouched legal h4, selector-window, 2,113-task, exhaustive bounded development-
teacher, response-closed direct mechanism, and caller-owned legal fallback
retain their prior meanings. ADR-0351 requires the tie-aware legal h4 affine-
envelope. ADR-0352 remains closed before any fresh untouched tie-aware affine
result. ADR-0355's owner was invoke exactly once; ADR-0358 was invoke exactly
once. ADR-0382 preregistered the literal-45 config; ADR-0383 source-sealed it;
ADR-0384 closed it.

The inherited front-door trust chain remains explicit. ADR-0310 made native-
simplex robustness the next systems question. ADR-0311's directive is
Preregister the native-simplex robustness audit. ADR-0312's directive is Seal
the native-simplex audit compiler and corpora. ADR-0313's directive is Seal the
native-simplex audit runner before results. ADR-0314's decision is Retain the
native-simplex audit and reject the frozen gate. ADR-0315's directive is
Source-seal the artifact-only native-simplex gate correction. ADR-0316's
decision is Accept the corrected audit and bound replacement eligibility.
ADR-0317 separates solver classes; ADR-0318 binds HiGHS 1.12.0; ADR-0319
requires one public HiGHS-DS call per canonical task; and All 177 ordered
observations pass under ADR-0320. ADR-0321 preserves caller-owned legal
fallback, ADR-0322 returns research evidence or rejection with no action,
ADR-0324 remains value-unopened, and ADR-0325 was authorized exactly once.
ADR-0326/0327 govern the exhaustive bounded development-teacher; ADR-0328
retains it and the solver-free rebinder; ADR-0330 remains permanently closed;
ADR-0331's append-and-fsync discipline, ADR-0332's exclusive `xb` open, and
ADR-0333's No replacement sizing value was opened statement remain binding.
ADR-0334/0335 bind the 2,113-task non-replay chain; ADR-0336 records width
three; ADR-0337 owns the response-closed direct mechanism; ADR-0338 alone
records the selected development raise width; and ADR-0339 remains a finite
absence claim. ADR-0340's 192 prospective tasks remain distinct from ADR-0341's
94 accepted one-call arms and ADR-0343's 126 confirmation arms; ADR-0342 alone
authorized the retained confirmation. ADR-0344/0345 own the finite h4 responder-
raise keystone. ADR-0346/0347 lead only to responder-row growth; ADR-0348/0349
lead only to selector-window work. ADR-0350 opened selector-stable affine
integration; ADR-0351 replaced it with tie-aware legal h4 affine envelopes;
ADR-0352 is closed by ADR-0353; ADR-0354/0355/0356 own the factorized exact face
result; ADR-0357/0358/0359 own and close same-fixture integration; and ADR-0360/
0361/0362 alone own the untouched confirmation and assessment. ADR-0363 and
ADR-0365 remain consumed; ADR-0364 remains exactly `GetProcessMemoryInfo failed`;
ADR-0366 remains exactly `representation_rejected_before_target_allocation`
with zero target calls. ADR-0367 through ADR-0384 own and close the quotient
algebra, capacity, bounded CUDA, staged, liveness, validation, and literal-
target ladder. ADR-0384 retains the passing literal-45 result and opens only
the actual-context quotient bridge. ADR-0385 preregisters the actual-context
quotient bridge. ADR-0386 records the source-sealed actual-context quotient
bridge. ADR-0387 freezes the consumer-capacity seam; ADR-0388 records the
source-sealed CuPy-free consumer-capacity result; ADR-0389 remains the accepted
prospective actual-context quotient CUDA-consumer boundary; ADR-0390 rejects
its source seal; ADR-0391 remains an accepted prospective bounded-arithmetic
boundary and freezes the first paired-tile boundary; ADR-0392 remains the accepted prospective preregistration-completeness correction and
corrects its pre-source arithmetic completeness; ADR-0393 remains the accepted bounded-device source-seal rejection and retains the first
implementation as a wall rejection; ADR-0394/0395 freeze the work and resource
questions; ADR-0396 through ADR-0403 own and close the three consumed preflight
owners; ADR-0404 through ADR-0406 own and close the exact-cubin diagnostic;
ADR-0407 through ADR-0409 own and close its empty artifact selector; ADR-0410
freezes only the suffix diagnostic; ADR-0411 source-seals it without operation;
ADR-0412 retains its sole result; ADR-0413 opens V4 prospectively; ADR-0414
corrects its bounded evidence envelope only; ADR-0415 seals the composite
source without running it; ADR-0416 retains its sole capacity rejection; and ADR-0417 prospectively freezes only the shared selected direct oracle. No earlier owner is revived.

For machine-checked continuity, ADR-0317's directive remains Separate solver
classes and prioritize the certified sizing adapter. All 177 ordered
observations pass under ADR-0320, making the separate consumer eligible.
ADR-0326 and ADR-0327 govern the exhaustive bounded development-teacher chain.
ADR-0328 retains that exhaustive teacher and solver-free rebinder. ADR-0334 and
ADR-0335 bind the 2,113-task non-replay chain. ADR-0344 and ADR-0345 own the
finite h4 legal responder-raise keystone line. ADR-0346 and ADR-0347 lead only
to responder-row growth. ADR-0348 and ADR-0349 lead only to selector-window
work. ADR-0351 requires the tie-aware legal h4 affine-envelope. ADR-0354 through
ADR-0359 own the factorized face and affine consumer chain. ADR-0380 freezes
the complete ordered populations 10 and 22. ADR-0383's owner was invoke exactly
once and remains consumed by ADR-0384. ADR-0417 imports neither that owner nor its target. The phrases exclusive untouched legal h4, selector-window,
2,113-task, exhaustive bounded development-teacher, response-closed direct
mechanism, and caller-owned legal fallback retain their prior meanings.

The exact historical continuity strings remain explicit. ADR-0328 retains the
exhaustive teacher and solver-free rebinder before the direct closed finite-
block greedy line. ADR-0351 requires the tie-aware legal h4 affine-envelope.
ADR-0352 remains closed before any fresh untouched tie-aware affine result.
ADR-0353 precedes ADR-0354's factorized exact active-set directional-face
diagnostic. ADR-0355's owner was invoke exactly once; ADR-0356 retains that
directional-face diagnostic before tie-aware affine integration. ADR-0357
requires an exclusive legal h4 owner, ADR-0358 was invoke exactly once, and
ADR-0359 requires a fresh value-unopened confirmation. ADR-0382 preregistered
the literal-45 config; ADR-0383 source-sealed it; ADR-0384 closed it.

The generated-front-door historical labels also remain literal. ADR-0328
precedes the direct closed finite-block greedy line. ADR-0367 preregisters the
occupied-card quotient. ADR-0368 seals the exact bounded algebra keystone.
ADR-0369 freezes the source-only arithmetic boundary. ADR-0370 seals the
numeric-array and logical-work result. ADR-0378 freezes the source-only literal-
target liveness boundary. ADR-0379 retains the 244,970,204-byte margin.
ADR-0381 source-seals the one-shot literal-45 CUDA owner. ADR-0388 records a
source-sealed CuPy-free consumer-capacity result.

## Kill criteria

Kill the mechanism if the query output is emitted before the last compatible
source row; if any boundary pair byte differs; if source-rank, logical-feature,
fold-feature, query-weight, or pair-product order changes; if a separate query
traversal remains in the population path; if storage aliases; if work is
hidden under copy or fold labels; if the source builder changes any parent span
besides the direct fold kernel; or if source-seal work imports CuPy, compiles,
loads, launches, reads/creates a result, or changes any numerical, resource,
wall, projection, action, quality, or claims threshold.

## Claims boundary

ADR-0417 preregisters one exact validation-work common-subexpression
elimination. It contains no successor source result, no device differential,
no complete 10/22 successor result, no capacity projection, no complete
25-card numerical value, no actual 45-card value, no resolver iteration, no
solve, no action, no 15-second result, no decision-quality claim, no
truncation authority, no blueprint result, and no poker-strength claim.
Systems and validation-work arithmetic remain no quality prior.

Stated literally for the claims gate: there is no complete 25-card numerical value.
