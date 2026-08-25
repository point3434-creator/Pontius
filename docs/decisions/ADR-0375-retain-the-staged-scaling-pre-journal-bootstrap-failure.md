# ADR-0375: Retain the staged-scaling pre-journal bootstrap failure

- Status: accepted retained first-invocation infrastructure failure; ADR-0374's clean v1 owner is permanently closed after its exclusive journal open found the frozen result parent absent, with no result bytes, header, GPU stage call, staged admission, timing, throughput, or literal 45-card result
- Date: 2026-08-25
- Follows: ADR-0374
- Invoked source commit: `898ed38afa1ae9fd062035b11a5529f8db9017a1`
- Command: `python -B -m pontius.gpu_quotient_staged_scaling_runner`
- Exception: `FileNotFoundError: journal parent directory does not exist`
- Failure site: `DurableEvidenceJournalWriter.create` before header append and before the runner enters its stage loop
- Result: `artifacts/gpu_occupied_card_quotient_staged_scaling_v1.jsonl` (absent after invocation)
- Partial result: `artifacts/gpu_occupied_card_quotient_staged_scaling_v1.jsonl.partial` (absent after invocation)
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0375
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Preserve the clean ADR-0374 source and permanently closed v1 path, then source-seal an additive v2 owner with a tracked hash-bound output parent, a new exclusive result path, the identical ADR-0373 stage science, bootstrap-preflight controls, and a reader that binds the v1 failure; do not retry v1, call a GPU stage before the v2 seal, create a literal 45-card path, or infer action-clock, quality, truncation, or strength
- Front-Door-Blockers: no staged-width GPU quotient result, source-sealed bootstrap-safe v2 owner, literal 45-card live-memory admission, literal scalable full-width contraction, certified truncation mechanism, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Question

What did ADR-0374's sole v1 invocation establish, and may the missing parent
directory be created followed by a retry?

## Decision

Retain the invocation as a pre-journal infrastructure failure and permanently
close v1. Do not create `artifacts/` and rerun the same owner. No durable bytes
exist to repair, backfill, or rename into a terminal.

The exact failure was:

```text
FileNotFoundError: journal parent directory does not exist
```

The source first called `DurableEvidenceJournalWriter.create` at the frozen
result path. That primitive checked `path.parent.is_dir()` and raised before
opening a file. The runner constructed no writer, appended no header, and had
not yet entered the `for cards in STAGE_CARDS` loop. Therefore zero staged GPU
calls follow from the sealed call order. This is source-backed control-flow
evidence, not a device observation. Both result paths remain absent.

The inherited front-door trust chain remains explicit. ADR-0310 made native-
simplex robustness the next systems question. ADR-0311's directive is
Preregister the native-simplex robustness audit. ADR-0312's directive is Seal
the native-simplex audit compiler and corpora. ADR-0313's directive is Seal the
native-simplex audit runner before results. ADR-0314's decision is Retain the
native-simplex audit and reject the frozen gate. ADR-0315's directive is
Source-seal the artifact-only native-simplex gate correction. ADR-0316's
decision is Accept the corrected audit and bound replacement eligibility.
ADR-0317's directive is Separate solver classes and prioritize the certified
sizing adapter. ADR-0318 binds HiGHS 1.12.0, ADR-0319 requires one public
HiGHS-DS call per canonical task, and All 177 ordered observations pass under
ADR-0320, making the separate consumer eligible. ADR-0321 preserves
caller-owned legal fallback, ADR-0322 returns research evidence or rejection with no
action, ADR-0324 remains value-unopened, and ADR-0325 was authorized exactly
once. ADR-0326 and ADR-0327 govern the exhaustive bounded development-teacher
chain. ADR-0328 retains that exhaustive teacher and solver-free rebinder
before the direct closed finite-block greedy line. ADR-0330 remains
permanently closed; ADR-0331's append-and-fsync discipline, ADR-0332's
exclusive `xb` open, and ADR-0333's statement that No replacement sizing value
was opened remain authoritative. ADR-0334 and ADR-0335 bind the 2,113-task
non-replay chain; ADR-0336 records width three; ADR-0337 owns the
response-closed direct mechanism; and ADR-0338 alone records the selected development
raise width. ADR-0339's exact comparison remains a finite absence claim.
ADR-0340's 192 prospective tasks remain distinct from ADR-0341's 94 accepted
one-call arms and ADR-0343's 126 confirmation arms; ADR-0342 alone authorized
that retained confirmation invocation. ADR-0344 and ADR-0345 own the finite
h4 legal responder-raise keystone line. ADR-0346 and ADR-0347 lead only to
responder-row growth; ADR-0348 and ADR-0349 lead only to selector-window work.
ADR-0350 opened selector-stable affine integration as a question; ADR-0351
replaced it with the tie-aware legal h4 affine-envelope requirement. ADR-0352's
owner is closed by ADR-0353 before any fresh untouched tie-aware affine result.
ADR-0354 source-seals the factorized exact active-set directional calculus;
ADR-0355's owner is closed by ADR-0356. ADR-0357 seals the factorized affine
consumer and requires an exclusive legal h4 owner. ADR-0358 owns its one same-
fixture integration invocation, and ADR-0359 permanently closes it while
requiring a fresh value-unopened confirmation. ADR-0360 fixes that population;
ADR-0361 owns and consumes the sole invocation; ADR-0362 alone performs the
artifact-only scientific assessment. ADR-0363 owns and consumes the sole v1
full-width capacity invocation; ADR-0364 retains its pre-capacity typed
failure; ADR-0365 owns and consumes the sole v2 capacity invocation; ADR-0366
retains its exact representation rejection. ADR-0367 preregisters and
ADR-0368 seals the bounded quotient algebra; ADR-0369 preregisters and
ADR-0370 seals only the source byte/work model. ADR-0371 preregisters and
ADR-0372 seals only the complete ten-card GPU mechanism. ADR-0373 freezes the
staged population, ADR-0374 source-seals v1, and ADR-0375 permanently closes
its first invocation before the journal. No earlier owner is revived.

ADR-0363 and ADR-0365 remain permanently consumed. ADR-0364 remains the
`GetProcessMemoryInfo failed` terminal. ADR-0366 remains
`representation_rejected_before_target_allocation` with zero target calls.
The required lifecycle markers remain invoke exactly once, exclusive untouched
legal h4, selector-window, 2,113-task, and caller-owned legal fallback.

## Failure classification

This is rejected-invocation tax, not a scientific stage rejection. The config,
source hashes, Git cleanliness, and absence checks passed. The first mutation
was the command itself. It failed in plumbing before any numerical population,
live-memory admission, or timing was opened.

ADR-0374's synthetic exclusive-create tests used temporary paths whose parent
directories already existed. Its real-path absence test asserted only that the
two files were absent; it did not assert that the frozen parent directory was
present and source-controlled. That seam allowed every source test to pass
while the real owner could not create its first record.

The structural correction is not `mkdir` immediately before retry. A successor
must use a new owner and result identity, bind a tracked parent artifact by
hash, verify that parent before any one-shot authority is consumed, exercise
the literal public path under a no-stage preflight control, and keep writer
creation inside a lifecycle whose failure classification is explicit.

## Kill criteria for a successor

Kill the successor if it edits or invokes the v1 runner; reuses the v1 result
path; creates the parent only after starting the one-shot campaign; fails to
hash-bind the tracked parent artifact; permits a missing-parent synthetic test
to call a stage; changes any stage, tolerance, sample, work, allocation,
runtime, wall, stop, or claims field; or treats v1's zero-stage failure as a
staged capacity result.

## Claims boundary

ADR-0375 establishes only one infrastructure fact: the sole v1 command could
not open its journal because the parent directory was absent. It supplies no
GPU stage, admission, numerical, timing, throughput, literal 45-card capacity,
solve, action, decision-quality, truncation, or poker-strength result. The
absence of a durable terminal is part of the retained defect, not permission
to reconstruct one or retry.
