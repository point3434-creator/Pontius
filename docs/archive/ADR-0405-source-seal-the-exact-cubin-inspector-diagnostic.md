# ADR-0405: Source-seal the exact-cubin inspector diagnostic

- Status: accepted source seal; the device-free importer, exact compile adapter, ACK-gated cubin-first child, five-command binary capture, exclusive durable owner, standard-library reader, and 15 corrected adversarial controls are hash-bound before any real CUDA diagnostic child, cubin, external inspector result, calibration, population, phase, projection, selected inspector, resource gate, capacity, action, quality, truncation, blueprint, or strength result
- Date: 2026-08-26
- Follows: ADR-0404
- Config: `experiments/configs/legal-river-exact-cubin-inspector-diagnostic-v1.json`
- Config canonical-LF SHA-256: `d52ac02e83f71cb50b6a61e8a9dd18403171e4ddd25227b2036bb61c2085fe8a`
- Diagnostic canonical-LF SHA-256: `3e8067a445952e20a3258ffae9c08c6fa228f971be5b28b462de08fa52862a1c`
- Owner canonical-LF SHA-256: `6afdc6fbcda751ba0d0b6bd4aa7d7f89449dd9e84cf62e1cd634d3291db5ee7b`
- Reader canonical-LF SHA-256: `ec7308b8adb8bd398844b60a2a149198262e53cfe9bd8256ba424e47bf87093b`
- Controls canonical-LF SHA-256: `cd53c2b73ae4097b8efe82baa981ab9828f1b02e1ebb253b60e35ce6a6d16c6d`
- Immutable scientific source canonical-LF SHA-256: `652a4a37cd097a92829364f1ec6976a6f31a4092ab9fc3e0f97a992e2565c4aa`
- Corrected focused controls: `15 passed`
- Durable-journal regressions: `8 passed`
- Real device-free literal protocol children: complete probe, silent-after-handshake deadline, and post-terminal rejection passed
- Real CUDA diagnostic-child calls: `0`
- Prospective diagnostic result: absent
- Reserved actual result: absent
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0405
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: From the clean ADR-0405 source-seal commit, invoke exactly once and with no arguments `python -B -m pontius.legal_river_exact_cubin_inspector_diagnostic_runner`; retain its first terminal and exact journal without retry, resume, skip, continuation, parser selection, or causal invention; independently rebind every cubin/stdout/stderr blob and candidate outcome; then write the diagnostic outcome ADR while leaving `selected_inspector`, every resource gate, calibration, population, projection, actual result, latency, action, quality, truncation, blueprint, and strength claim null
- Front-Door-Blockers: no retained exact-cubin diagnostic corpus, qualified inspector, resource-gate verdict, retained 10/22-card calibration, conservative complete-25 capacity verdict, complete 25-card numerical result, actual owner, or full-width actual-context quotient value exists; v1, v2, and v3 remain permanently consumed; no general odd-chip or side-pot leaf automaton, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Question

Does the ADR-0404 implementation now preserve the exact cubin and every raw
candidate outcome strongly enough to authorize one later diagnostic call
without opening inspector selection or calibration?

## Decision

Yes. Source-seal the diagnostic and authorize exactly one later no-argument
invocation from a clean commit. This decision contains no CUDA diagnostic
outcome, cubin, inspector result, resource value, or capacity result.

Importing diagnostic, owner, and reader code is device-free. The only real
compile entry is local to `run_real_diagnostic`: it verifies the immutable
scientific file and embedded CUDA-source hashes, exact five caller options,
empty module/kernel/cubin caches, absent-or-false `CUPY_COMPILE_WITH_PTX`, and
then calls only the unchanged `_kernels(cp)` path. It never calls
`run_calibration_preflight` or constructs any population fixture.

The child exposes CuPy's internal architecture option and output method,
requires direct ELF cubin output, loads all fifteen immutable kernels, and
captures the three direct driver rows. Runtime evidence is exact-type and
meaning-typed: device name, compute capability, and CuPy version are nonempty
strings; byte count and CUDA versions are nonnegative integers. Generic object
conversion is absent.

### Durability handshake

Every child frame requires a parent ACK carrying its ordinal and fresh
challenge. The parent sends that ACK only after constructing the observation,
appending it, flushing, and fsyncing it through the durable journal writer.
Thus the child cannot create the inspector temporary or run command one until
the complete base64 cubin, raw SHA-256, byte count, driver rows, runtime, and
compile identity are durable. It cannot run command `k+1` until command `k` is
durable, and it deletes the temporary cubin only after every attempted command
event is acknowledged. Cleanup and terminal evidence are then separately
acknowledged.

The subprocess controller drains stderr concurrently, reads stdout through a
bounded queue, keeps the laboratory deadline live while stdout remains open
and silent and after stdout EOF, rejects noncanonical frames and all
post-terminal output, closes pipes, and kills/joins on every exception. A
deadline recheck occurs after every durable append and before its ACK, then
again at stdout EOF and process exit, so a late fsync cannot authorize more
child work. A
literal device-free child proves complete handshake→cubin→five-command→cleanup
→terminal flow. A second literal child stays silent after its acknowledged
handshake and is killed by the parent wall. A third receives an ACK for
terminal evidence and then emits one more frame; the parent rejects it.

### Binary and journal bounds

The command runner uses `Popen`, `check`-free byte streams, concurrent bounded
drains, explicit timeout/termination, and exact captured prefixes. Nonzero
return code remains `completed`; only timeout or output overflow is a typed
candidate rejection. Binary envelopes use canonical base64 plus decoded byte
count and SHA. Reader controls include NUL and invalid UTF-8 octets.

The 48 MiB journal cap is not approximated by a second threshold. Before each
observation, the owner constructs the exact prospective durable envelope and a
worst-case 4,096-ASCII-byte outer terminal envelope using the current sequence
and line hash. It refuses the observation before overflow if both cannot fit.
The terminal therefore remains durably bindable. The 180-second laboratory
wall begins at diagnostic-function entry, so compilation is included. A
command that returns only after its own 30-second wall is typed timeout even if
the OS process has already exited.

### Independent reader

The reader imports only the standard library and the durable journal. It
recovers the exact prefix, rejects any suffix, rebinds current source hashes
and all three retained artifacts, verifies event/commit/candidate order,
decodes and rehashes every cubin/stdout/stderr blob, requires ELF magic and all
three driver-row identities, and reconstructs the fixed kernel order from an
exact key set. It accepts nonzero command codes as raw capture only and never
selects an inspector. A complete capture is exactly ten observations plus
header and outer terminal; every candidate must be transport-complete, but its
return code may be nonzero.

### Rejected pre-seal runs and corrections

The first 13-control run had one real error. Canonical JSON sorts mapping keys,
but the reader demanded the producer's incidental direct-driver mapping
iteration order. The correction validates the exact three-key inventory and
reconstructs the frozen tuple order explicitly. Traversal order is not evidence
semantics.

The first 15-control transport run then exposed one cleanup defect and one bad
control price. The silent-child wall was 75 ms, so ordinary process startup
could expire before the handshake; the exceptional parent path also killed the
child without closing its stdin writer, producing a `ResourceWarning`. The
corrected control uses a one-second wall to isolate post-handshake silence, and
the parent closes stdin on every exceptional path. With `ResourceWarning`
promoted to error, all 15 focused controls pass.

A subsequent audit found two latent accounting errors before value. The local
laboratory wall began after compilation, and independent 8 MiB blob caps did
not by themselves prove the complete 48 MiB journal would fit. The wall now
begins at function entry; exact prospective-envelope accounting, not a new
constant, reserves the final terminal. These were repaired before source seal,
CUDA compile, or result.

The passing suite also covers exact preregistration and absence locks,
fresh-import CuPy/science absence, static no-calibration/no-consumed-owner call
graphs, non-UTF-8 binary identity, nonzero stdout/stderr retention, command
timeout/output limit, all-five-nonzero complete protocol capture, complete
synthetic journal and independent rebinding, worker failure before compile,
runtime/cubin/candidate/order/cleanup/status mutations, torn and post-terminal
suffixes, and exclusive replay. Eight durable-journal regressions pass beside
it. The public result and reserved actual path remain absent.

The inherited front-door trust chain remains explicit. ADR-0310 made native-
simplex robustness the next systems question. ADR-0311's directive is
Preregister the native-simplex robustness audit. ADR-0312's directive is Seal
the native-simplex audit compiler and corpora. ADR-0313's directive is Seal
the native-simplex audit runner before results. ADR-0314's decision is Retain
the native-simplex audit and reject the frozen gate. ADR-0315's directive is
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
absence claim. ADR-0340's 192 prospective tasks remain distinct from
ADR-0341's 94 accepted one-call arms and ADR-0343's 126 confirmation arms;
ADR-0342 alone authorized the retained confirmation. ADR-0344/0345 own the
finite h4 responder-raise keystone. ADR-0346/0347 lead only to responder-row
growth; ADR-0348/0349 lead only to selector-window work. ADR-0350 opened
selector-stable affine integration; ADR-0351 replaced it with tie-aware legal
h4 affine envelopes; ADR-0352 is closed by ADR-0353; ADR-0354/0355/0356 own
the factorized exact face result; ADR-0357/0358/0359 own and close same-fixture
integration; and ADR-0360/0361/0362 alone own the untouched confirmation and
assessment. ADR-0363 and ADR-0365 remain consumed; ADR-0364 remains exactly
`GetProcessMemoryInfo failed`; ADR-0366 remains exactly
`representation_rejected_before_target_allocation` with zero target calls.
ADR-0367 through ADR-0384 own and close the quotient algebra, capacity,
bounded CUDA, staged, liveness, validation, and literal-target ladder.
ADR-0368 seals only the exact bounded algebra keystone for the occupied-card
quotient within that chain. ADR-0369 is the source-only arithmetic boundary.
ADR-0370 seals the numeric-array and logical-work result. ADR-0378 remains the
accepted prospective source-only literal-target liveness and streamed-
validation boundary, and ADR-0379 retains its 244,970,204-byte device-cap
margin without live admission. ADR-0381 source-seals the bounded validation
seam before the one-shot literal-45 CUDA owner. ADR-0385 froze the legal bridge question;
ADR-0386 source-sealed only its host answer; ADR-0387 froze the consumer-
capacity question; ADR-0388 source-sealed only that CuPy-free answer; ADR-0389
froze the additive CUDA-consumer question; ADR-0390 rejected its source seal;
ADR-0391 froze the first paired-tile boundary; ADR-0392 corrected its pre-
source arithmetic completeness; ADR-0393 retained the first implementation as
a wall rejection; ADR-0394/0395 freeze the work and resource questions;
ADR-0396 through ADR-0403 own and close the three consumed preflight owners;
ADR-0404 freezes this diagnostic; and ADR-0405 source-seals it. No earlier
owner is revived.

For machine-checked continuity, ADR-0317's directive remains Separate solver
classes and prioritize the certified sizing adapter. All 177 ordered
observations pass under ADR-0320, making the separate consumer eligible.
ADR-0326 and ADR-0327 govern the exhaustive bounded development-teacher
chain. ADR-0328 retains that exhaustive teacher and solver-free rebinder.
ADR-0334 and ADR-0335 bind the 2,113-task non-replay chain. ADR-0344 and
ADR-0345 own the finite h4 legal responder-raise keystone line. ADR-0346 and
ADR-0347 lead only to responder-row growth. ADR-0348 and ADR-0349 lead only
to selector-window work. ADR-0351 requires the tie-aware legal h4 affine-
envelope. ADR-0354 through ADR-0359 own the factorized face and affine
consumer chain. ADR-0380 freezes the complete ordered populations 10 and 22.
ADR-0383's owner was invoke exactly once and remains consumed by ADR-0384.
ADR-0405 imports neither that owner nor its target. The phrases exclusive
untouched legal h4, selector-window, 2,113-task, exhaustive bounded
development-teacher, response-closed direct mechanism, and caller-owned legal
fallback retain their prior meanings.

The exact historical continuity strings remain explicit. ADR-0328 retains the
exhaustive teacher and solver-free rebinder before the direct closed
finite-block greedy line. ADR-0351 requires the tie-aware legal h4 affine-envelope.
ADR-0352 remains closed before any fresh untouched tie-aware affine result.
ADR-0353 precedes ADR-0354's factorized exact active-set directional-face
diagnostic. ADR-0355's owner was invoke exactly once; ADR-0356 retains that
directional-face diagnostic before tie-aware affine integration. ADR-0357
requires an exclusive legal h4 owner, ADR-0358 was invoke exactly once, and
ADR-0359 requires a fresh value-unopened confirmation. ADR-0382 preregistered
the literal-45 config; ADR-0383 source-sealed it; ADR-0384 closed it.

### Invocation boundary

The result remains absent. Source-seal controls may repeat only device-free
protocol modes. After this source-seal commit, the public owner may be called
exactly once. Any compile, module, runtime, tool, timeout, output, journal,
cleanup, or infrastructure terminal is final. No learned exception authorizes
a replay.

### Claims boundary

ADR-0405 proves only that the exact-cubin diagnostic is source-sealed and its
device-free controls pass. It supplies no actual cubin, tool return code,
inspector output, selected inspector, resource row or gate, calibration,
population value, phase timing, projection, complete 25-card value, actual
45-card value, resolver iteration, solve, action, 15-second result, decision
quality, truncation, blueprint, or poker strength. Systems evidence remains no
quality prior.
