# ADR-0406: Retain the exact-cubin inspector diagnostic

- Status: accepted retained diagnostic capture; the sole ADR-0405 invocation durably preserves one exact driver-loadable ELF-magic payload, all three direct-kernel driver rows, both CUDA 13.3 tool identities, all three nonzero payload-operation outcomes, cleanup, and the first terminal, while `selected_inspector`, every resource gate, calibration population, phase, projection, complete 25-card numerical value, actual 45-card value, action, quality, truncation, blueprint, and strength result remain null
- Date: 2026-08-26
- Follows: ADR-0405
- Invoked source commit: `596a90e92285e04ec9e7e3e2f68b22cb195aa46b`
- Command: `python -B -m pontius.legal_river_exact_cubin_inspector_diagnostic_runner`
- Terminal: `capture_complete`
- Capture pass: `True` (transport completeness only)
- Result: `artifacts/work_preflight/legal_river_exact_cubin_inspector_diagnostic_v1.jsonl`
- Result bytes: `705101`
- Result SHA-256: `9e0d160dd36884adb85914f819e11882d5becc42071f7847c1503a42c1d83aed`
- Journal records: `12` (`header`, ten ordered observations, `terminal`)
- Cubin-labeled payload bytes: `514039`
- Cubin-labeled payload SHA-256: `5dc4973302061b29dccd955ff7ee4dff3d61216316fb5d2fa71e9df22f42cd97`
- Reserved actual result: absent
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0406
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Preserve the immutable 12-record diagnostic and permanently closed ADR-0405 owner, then preregister a GPU-free artifact-only semantic selector before writing selector source or interpreting a candidate as authoritative: bind the exact journal SHA, decode and rehash only its retained payload and raw streams, freeze candidate-specific parsers and exact three-direct-kernel row requirements, keep ELF magic distinct from external-tool inspectability, require conservative agreement with the retained driver rows before any inspector can qualify, and type the empty result as `no_qualified_inspector`; do not invoke CUDA, CuPy, either external tool, any consumed owner, calibration, a population fixture, the reserved actual owner, or infer resource passage, capacity, latency, action quality, truncation, blueprint value, or poker strength
- Front-Door-Blockers: no semantically qualified exact-binary inspector, resource-gate verdict, retained 10/22-card calibration, conservative complete-25 capacity verdict, complete 25-card numerical result, actual owner, or full-width actual-context quotient value exists; the three work-preflight owners and exact-cubin diagnostic owner are permanently consumed; no general odd-chip or side-pot leaf automaton, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Question

What did the sole exact-cubin diagnostic establish, and may its transport pass
be promoted directly into an inspector or resource-gate decision?

## Decision

Retain the exact 12-record artifact and permanently close the diagnostic owner.
The first invocation completed its capture protocol in approximately 3.5
seconds. That wall is diagnostic lifecycle time, not primitive, iteration,
solve, per-street, or action latency. The independent standard-library reader
reconstructs:

```text
terminal=capture_complete
passed=True
event_count=10
source_commit=596a90e92285e04ec9e7e3e2f68b22cb195aa46b
journal_byte_count=705101
selected_inspector=null
resource_gate_result=null
calibration_result=null
capacity_projection=null
```

`passed=True` means only that every frozen byte-capture and lifecycle event is
present and internally consistent. It is not a semantic-inspector pass.

The journal binds clean source provenance and the unchanged five caller
options. CuPy reports its additive internal `-arch=sm_120` option and output
method `cubin`. The retained 514,039-byte payload begins with the four ELF
magic bytes, hashes to
`5dc4973302061b29dccd955ff7ee4dff3d61216316fb5d2fa71e9df22f42cd97`,
loads through the CUDA driver, exposes all fifteen named kernels, and yields
these direct driver rows:

| Kernel | Registers | Local bytes | Shared bytes | Maximum threads/block |
|---|---:|---:|---:|---:|
| `direct_selected_queries_tile` | 38 | 128 | 0 | 1024 |
| `direct_selected_fold_tile` | 48 | 1024 | 0 | 1024 |
| `direct_selected_adjoint_tile` | 38 | 128 | 0 | 1024 |

Those are retained driver observations. They do not satisfy ADR-0395's dual-
instrument rule by themselves.

### Exact candidate outcomes

Both installed tools identify themselves as CUDA compilation tools release
13.3, version 13.3.73, build `cuda_13.3.r13.3/compiler.38244171_0`. Their raw
streams are retained as base64 with decoded length and SHA-256 and were
independently decoded and rehashed.

| Candidate | Return code | Raw outcome |
|---|---:|---|
| `cuobjdump --version` | 0 | 239 stdout bytes, SHA-256 `0d900ec8923253a1586ebd9fea439eb1d0d52bcd532e8b06df2071feac27728a` |
| `cuobjdump --dump-resource-usage PAYLOAD` | 4294967295 | 109 stdout bytes, SHA-256 `cf5e9060b57eabd23f323a88237eb75614cc8f9bd97b9b1223fb6752305cc65e`; reports that the temporary file does not contain device code |
| `cuobjdump --dump-elf PAYLOAD` | 4294967295 | the same 109 stdout bytes and SHA-256; reports that the temporary file does not contain device code |
| `nvdisasm --version` | 0 | 232 stdout bytes, SHA-256 `8a472727cf36f6014e49d972c82cb77ac3227fb598ad14ba30ade9d25270f0a2` |
| `nvdisasm PAYLOAD` | 1 | zero stdout bytes and 100 stderr bytes, SHA-256 `d20af6945a88e3f00b52c88d17227228436c28a21f10109a0d6d695bb2450b6e`; reports an invalid ELF file |

All five events are transport-complete. The temporary payload was removed only
after all five events were durably acknowledged. Nonzero returns were evidence,
not exceptions, so ADR-0403's erased-stream defect is retired for this
diagnostic.

The facts are deliberately left in tension. The retained bytes have ELF magic
and were accepted by the driver, while the two offline tools produced the
quoted classifications. ADR-0406 does not infer malformed bytes, an SM120
tool defect, an ELF-container subtype, an embedded representation, a driver
transformation, or any other cause. ELF magic is now known to be insufficient
evidence of external-tool inspectability on this path. Tool `--version`
success is again known to be insufficient evidence that its payload operation
works.

### Successor boundary

Selection remains a separate prospective question. The next ADR must bind the
immutable artifact before selector source and freeze a GPU-free, artifact-only
reader. Candidate-specific acceptance must be mechanical and must require the
requested semantic rows for every direct kernel, not merely zero status,
recognizable magic, or nearby metadata. Any candidate row must be compared
conservatively with the retained driver row before qualification. If no
candidate meets the frozen rule, the typed result is
`no_qualified_inspector`; no fallback to driver-only evidence is permitted.

The selector may not invoke CuPy, CUDA, `cuobjdump`, `nvdisasm`, compilation,
or any consumed owner. It may not repair, normalize, regenerate, or replace
the retained bytes. A later mechanism that needs fresh compilation or another
external operation requires another prospective research decision after the
artifact-only selector closes.

### Invocation ledger

Four related one-shot invocations are now consumed before calibration. V1
failed worker bootstrap, V2 failed while serializing a typed antecedent, V3
retained the external resource-command rejection, and this diagnostic retained
the missing cubin and raw streams successfully. Their journals total
`5322 + 8508 + 15783 + 705101 = 734714` bytes. The shared runner and diagnostic
handshake have progressively retired bootstrap, serializer, and evidence-loss
defects, but they have not established an operational dual resource
instrument. Kill criteria and claim boundaries remain honored: no owner was
replayed, no threshold moved, and no result was promoted beyond its type.

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
seam before the one-shot literal-45 CUDA owner. ADR-0385 froze the legal bridge
question; ADR-0386 source-sealed only its host answer; ADR-0387 froze the
consumer-capacity question; ADR-0388 source-sealed only that CuPy-free answer;
ADR-0389 froze the additive CUDA-consumer question; ADR-0390 rejected its
source seal; ADR-0391 froze the first paired-tile boundary; ADR-0392 corrected
its pre-source arithmetic completeness; ADR-0393 retained the first
implementation as a wall rejection; ADR-0394/0395 freeze the work and resource
questions; ADR-0396 through ADR-0403 own and close the three consumed preflight
owners; ADR-0404 freezes the diagnostic; ADR-0405 source-seals it; and
ADR-0406 retains its sole invocation. No earlier owner is revived.

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
ADR-0406 imports neither that owner nor its target. The phrases exclusive
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

## Claims boundary

ADR-0406 establishes exact capture, driver-loadable named kernels, the retained
driver rows, the five raw CUDA 13.3 command outcomes, cleanup, and the first
terminal. It establishes no selected or qualified inspector, cubin resource
row, resource-gate verdict, exact spill traffic, calibration, phase timing,
projection, complete 25-card value, actual 45-card value, resolver iteration,
solve, action, 15-second result, decision quality, truncation authority,
blueprint value, or poker strength. Systems evidence remains no quality prior.
