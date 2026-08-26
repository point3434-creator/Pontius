# ADR-0414: Correct the V4 bounded-evidence envelope before source

- Status: accepted prospective pre-source evidence-envelope correction; ADR-0413's four possible 8 MiB command streams now use exact chunked retention inside a 64 MiB journal, while much smaller strict-ASCII parser-admission bounds keep the unchanged one-line scientific event within its 1 MiB transport ceiling; every exact repair, executed-byte, resource formula, threshold, scientific population, phase, ratio, wall, lifecycle, partial-outcome, kill, and claims field remains binding, and every V4 probe, real compilation, resource gate, calibration, projection, complete 25-card numerical value, actual 45-card value, action, quality, truncation, blueprint, and strength result remains unopened
- Date: 2026-08-26
- Follows: ADR-0413
- Base config: `experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-owner-v4.json`
- Base config canonical-LF SHA-256: `80aad86a806275c4b8979025237b555332e97a84ec1090845ee12616701b4b43`
- Correction config: `experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-owner-v4-envelope-correction-v2.json`
- Correction config canonical-LF SHA-256: `f4fdb2e89809f4c22422aed883b6d9f1bbb2e1aea6c32dfcf536f7a27d111ab7`
- ADR-0413 canonical-LF SHA-256: `73e2142de693cf2a801af0a60674c24192d9b957542b9aaaa571c0e6951f5bec`
- Preregistration commit: `795e8a80599d0a16f3c723dac040dfe26700f834`
- Successor drafts: present only as uncommitted, uninvoked mechanical source drafts
- Prospective result: `artifacts/work_preflight/legal_river_quotient_cuda_compensated_work_preflight_v4.jsonl` absent
- Reserved actual result: `artifacts/legal_river_quotient_cuda_consumer_v1.jsonl` absent
- Actual V4 execution/allocation/scientific counters: `0/0/0`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0414
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement and source-seal only the composite ADR-0413/ADR-0414 V4 adapter, owner, reader, and controls without creating the real result: load and hash both configs; preserve the exact repair-before-load and same-executed/inspected-byte seam; retain both streams from both external commands losslessly in ordered 196,608-byte chunks under independent 8 MiB caps and a 64 MiB journal; apply 32,768-byte combined-version and 262,144-byte resource-stdout parser-admission bounds only after raw retention; preserve the exact serializer, two-instrument 255/4,096 maxima, immutable 10/22 science, 16 phases, walls, and integer-only population-25 projection; prove chunk completeness, maximum-envelope arithmetic, line/journal/stream separation, unequal resource envelopes, hard row rejection, process-local restoration, and independent rebinding; keep the V4 and reserved actual result paths absent until a later clean committed invocation checkpoint
- Front-Door-Blockers: no composite V4 source seal, repaired-executed-cubin resource-gate verdict, retained 10/22-card calibration, conservative complete-25 capacity verdict, complete 25-card numerical result, actual owner, or full-width actual-context quotient value exists; all three earlier work-preflight owners and every cubin diagnostic owner are permanently consumed; no general odd-chip or side-pot leaf automaton, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Question

Can ADR-0413's bounded command evidence actually fit its own journal and child
transport in every admitted case?

## Decision

No as written. Correct the evidence envelope before source rather than letting
implementation silently truncate, conflate caps, or discover an impossible
failure journal during the first real invocation.

ADR-0413 admits two external commands, each with independently capped stdout
and stderr. Four streams at 8,388,608 bytes total 33,554,432 raw bytes. Their
lossless base64 alone requires 44,739,248 characters before JSON envelopes,
which cannot fit ADR-0413's 16,777,216-byte journal. Separately, one successful
8 MiB resource stdout cannot fit the unchanged 1,048,576-character child line
when the immutable scientific event repeats that raw text. These are arithmetic
contradictions, not implementation inconveniences.

Adopt the additive correction config as an overlay on all of ADR-0413. Replace
only the infeasible journal capacity and add the missing distinction between
capture and parser admission. No exact-repair predicate, compiler option,
module identity, resource quantity, formula, ceiling, resident-thread rule,
population, phase, ratio, wall, stop, lifecycle, partial-outcome rule, or claim
is changed.

### Lossless command retention

Keep the independent 8 MiB capture limit for each external stream. Encode each
stream as ordered chunks of at most 196,608 raw bytes, or at most 43 chunks at
the ceiling. Each chunk carries command identity, stream identity, ordinal,
raw byte count, total raw byte count, total stream SHA-256, and bounded base64.
The command terminal becomes interpretable only after every declared stdout
and stderr chunk is durable. Missing, duplicate, reordered, oversized, or
hash-inconsistent chunks reject.

Increase only the V4 journal cap to 67,108,864 bytes. Four maximum streams
require 44,739,248 base64 characters. At 43 chunks per stream and a frozen
4,096-byte maximum envelope allowance per chunk, the conservative retained-
stream reserve is 45,443,760 bytes, leaving 21,665,104 bytes for header,
provenance, handshake, probe, repair, command terminals, scientific rows, and
the owner terminal. Before every append, the writer must still calculate the
actual canonical line and reserve a worst-form infrastructure terminal; these
figures are admission ceilings, not permission to overrun the exact writer.

The child-line ceiling remains 1,048,576 characters. Chunking, not truncation,
makes raw evidence fit. Journal, stream, chunk, child-line, parser, and stderr
limits remain separate semantic quantities even where a numerical coincidence
later occurs.

### Parser admission after evidence

The 8 MiB stream cap answers how much raw evidence can be retained. It does not
answer how much output the fixed grammar or one-line scientific event may
consume. After all command streams are durable, require combined version text
at or below 32,768 bytes and resource stdout at or below 262,144 bytes. Accepted
text is strict ASCII containing only tab, LF, CR, and printable bytes 0x20
through 0x7e. This bounds JSON escaping by two and leaves the complete resource
event below the unchanged child-line ceiling.

An output may therefore be captured successfully but rejected for parser
admission. That is an honest typed terminal with full raw bytes retained; it is
not an output-limit failure and may not be retried. Parser ceilings may never
truncate or replace the capture limits.

### Why this is a correction, not scope growth

No source probe, real compiler, tool, driver, population, phase, or projection
was opened. The only V4 files are uncommitted mechanical drafts made after the
clean ADR-0413 commit; they confer no source authority and may be revised under
the composite contract. Both result paths remain absent. The correction is the
same pre-source discipline ADR-0395 used for the unavailable spill wording:
make the evidence contract feasible before any result can exploit ambiguity.

The source-seal controls must exercise four maximum synthetic streams in pure
reserve arithmetic, exact chunk round trips, one missing and one reordered
chunk, one overhead breach, child-line independence, parser boundaries at and
one byte above each ceiling, forbidden ASCII controls, and deliberately unequal
payload/stream/journal values. None may invoke CUDA or create the real result.

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
result; ADR-0413 freezes V4; ADR-0414 corrects only its evidence envelope before
source. No earlier owner is revived.

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
its source seal; ADR-0391 freezes the first paired-tile boundary; ADR-0392
corrects its pre-source arithmetic completeness; ADR-0393 retains the first
implementation as a wall rejection; ADR-0394/0395 freeze the work and resource
questions; ADR-0396 through ADR-0403 own and close the three consumed preflight
owners; ADR-0404 through ADR-0406 own and close the exact-cubin diagnostic;
ADR-0407 through ADR-0409 own and close its empty artifact selector; ADR-0410
freezes only the suffix diagnostic; ADR-0411 source-seals it without operation;
ADR-0412 retains its sole result; ADR-0413 opens V4 prospectively; and ADR-0414
corrects its bounded evidence envelope only. No earlier owner is revived.

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
once and remains consumed by ADR-0384. ADR-0414 imports neither that owner nor
its target. The phrases exclusive untouched legal h4, selector-window,
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

Kill a source seal that retains the 16 MiB journal, truncates a stream to fit a
line or journal, interprets before every declared chunk is durable, uses the
parser ceiling as a capture ceiling, shares any evidence-bound knob, or changes
any non-envelope ADR-0413 field. The original repair, resource, science, and
claims kill criteria remain binding.

## Claims boundary

This correction opens no V4 probe, compiler return, module, tool, resource
gate, calibration population, phase timing, projection, complete 25-card
numerical value, actual 45-card value, resolver iteration, solve, action,
15-second result, decision quality, truncation authority, blueprint result, or
poker-strength result. Systems evidence remains no quality prior.

Stated literally for the claims gate: there is no complete 25-card numerical value.
