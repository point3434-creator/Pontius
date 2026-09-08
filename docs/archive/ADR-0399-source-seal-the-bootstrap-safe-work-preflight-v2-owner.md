# ADR-0399: Source-seal the bootstrap-safe work-preflight v2 owner

- Status: accepted source-only bootstrap-safe v2 seal; the additive owner, new lifecycle journal, solver-free reader, shared bounded child transport, fresh-challenge no-CUDA handshake, immutable-v1 rebinding, and 16 focused controls pass while the v2 result remains absent, campaign mode has not run, the scientific source is unchanged, and no compiler observation, calibration value, phase row, projection, complete 25-card numerical value, actual 45-card value, action, quality, truncation, blueprint, or strength result is opened
- Date: 2026-08-25
- Follows: ADR-0398
- Config: `experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-owner-v2.json`
- Config canonical-LF SHA-256: `e7f2a60035aad77d20461b4e5288bd85375f751b2d9ec410d2f197cfcacaf334`
- V2 runner canonical-LF SHA-256: `cf232b8a84467bc5cd28911f45e75657a5fda220ed5e11ece84f2c054f4ad690`
- V2 solver-free reader canonical-LF SHA-256: `baaa4f9078fe580d53adf01f30d2dbc593df0c402072ea0157c892cc47c7f81e`
- V2 controls canonical-LF SHA-256: `b18757683e7e5f2ddd56d9328bab3ea844de6dd2d7da2d6bdb43ba069ef9eb36`
- Unchanged scientific source canonical-LF SHA-256: `652a4a37cd097a92829364f1ec6976a6f31a4092ab9fc3e0f97a992e2565c4aa`
- Immutable v1 runner canonical-LF SHA-256: `9949e3a0b82f6409f137531a03d36e960e6f4b33be808b27da4e2e2278d901d1`
- Immutable v1 reader canonical-LF SHA-256: `740013c40430c56ef1357ea9566532c1239f31c540280445032d9e367d8a9d76`
- Immutable v1 controls canonical-LF SHA-256: `cfeff758eebf81201536e26899fbdfc8c0d3b9857cf2e51e242878a1cda8f130`
- Immutable v1 result SHA-256: `fd8c71ddb534320577dfc9a390946fc3dffe3fe806bf93d456ac33e55fe8e830`
- V2 protocol SHA-256: `acb02281d28b05c60f789d73b92fd5ffffafdd16cfb684518b7db3d221d9452c`
- V2 campaign SHA-256: `e35538c197bb435d07cb59f390cb2a40c7d41fcbd35ae98f53b2f41aad2a7170`
- Literal worker module: `pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner`
- Focused source controls: `16 passed` in `2.504 s`, with `ResourceWarning` promoted to error
- Surrounding paired-science and durable-journal controls: `16 passed` in `25.544 s`
- Immutable v1 controls: `15 passed`, exactly three historical post-result absence predicates retained as expected failures
- V2 result: `artifacts/work_preflight/legal_river_quotient_cuda_compensated_work_preflight_v2.jsonl` absent
- Reserved actual result: `artifacts/legal_river_quotient_cuda_consumer_v1.jsonl` absent
- Campaign-child calls at this boundary: `0`
- Compiler/calibration/phase/projection calls at this boundary: `0/0/0/0`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0399
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: From the clean committed ADR-0399 source seal, verify the immutable v1 journal and absent v2/reserved paths, then invoke `python -B -m pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner` exactly once; retain its first exclusive append-and-fsync terminal without retry, repair, skip, continuation, or v1 revival; require the solver-free v2 reader to rebind the journaled fresh-challenge handshake and every unchanged scientific row; keep population 25 integer-projection-only and do not infer action-clock, quality, truncation, blueprint, or poker strength
- Front-Door-Blockers: no retained v2 10/22-card calibration, conservative complete-25 capacity verdict, complete 25-card numerical result, actual owner, or full-width actual-context quotient value; no general odd-chip or side-pot leaf automaton, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Question

Does the ADR-0398 implementation retire ADR-0397's worker-module defect through
the real process seam while keeping v1 immutable, campaign mode unopened, and
the complete capacity experiment scientifically unchanged?

## Decision

Yes at the source boundary only. Accept the additive v2 runner, reader, and 16
focused controls. The v2 result remains absent. The source seal ran a real
`-B -m` handshake child, but it did not select campaign mode, import CuPy or
the scientific source in that child, compile a kernel, construct a calibration
fixture, or create a durable result. Only a later clean commit may consume the
new owner once.

The worker command is literal, not contextual:

```text
python -B -m pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner
```

Handshake and campaign use the same `_run_child_process` function. That one
transport owns the Popen command, strict ASCII framing, a 64-entry bounded
stdout queue, concurrently drained 4,096-character stderr, exact monotonic
deadline, return-code and child-terminal checks, and pipe/thread cleanup. A
queue reader has explicit cancellation, stdout EOF does not stop the deadline
while the child remains alive, and any event after a child terminal rejects.
These are lifecycle controls shared automatically by the future scientific
child, not a parallel test-only path.

The real handshake uses `secrets.token_bytes(32)`. The child reports the
SHA-256 of that challenge, its literal `__spec__.name`, runtime name
`__main__`, package `pontius`, `-B` state, single argv entry, and absence of
both CuPy and the scientific module. The parent validates the response before
journaling a wrapper that contains its independently known challenge digest
beside the child payload. The reader reconstructs equality of those two
digests and all module/import facts; a stored pass bit is not enough.

The public owner writes and fsyncs its new header before config, Git, retained-
v1, handshake, or campaign work. It then binds the ADR-0398 config, a strict
clean Git boundary, all current dependency hashes, and ADR-0397's exact
5,322-byte three-record terminal. Provenance precedes the repeated real
handshake; scientific events cannot appear before that handshake. The full
handshake plus campaign shares the unchanged 240-second laboratory wall, and
campaign receives only the remaining allowance.

The v2 reader is standard-library and CuPy-free. It independently owns the v2
protocol, campaign, header, provenance, dependency set, retained-v1 bytes,
handshake, order, last-event identity, and terminal. Only afterward does it
construct an in-memory v1-shaped validation view of non-handshake events and
call the immutable v1 scientific rebinder with current-source trust disabled.
The v2 reader has already rebound every current dependency itself. The view is
never written, never claims a v1 producer, and cannot repair either journal.

No v1 owner code was imported. The successor source contains neither the v1
runner import nor `[sys.executable, "-B", "-m", __name__]`. The scientific
source, v1 runner, v1 reader, v1 controls, configs, and artifact retain their
ADR-0396/ADR-0397 hashes. The only code change is a new lifecycle owner and
reader around the unchanged scientific call.

The 16 focused controls cover fresh device-free import; exact config and v1
rebinding; additive source structure; the real cryptographically fresh child;
wrong/stale challenge response; CuPy and scientific-source import claims;
literal command construction; unframed and malformed stdout; bounded stderr;
nonzero return; exact timeout; event-after-terminal rejection; synthetic
complete scientific passage; pre-handshake and post-handshake infrastructure
terminals; challenge, dependency, and order mutations with full rehashing;
exclusive replay; v1 drift; torn suffix; reserved-actual presence; and public
no-argument/result-absence checks. `ResourceWarning` was an error. An initial
control run exposed unclosed pipe objects; the final transport closes them and
the warning-clean suite passes.

The immutable v1 test file remains unedited. Its 18 tests run with exactly the
three ADR-0397 historical pre-result predicates marked expected: fresh import
expects the consumed v1 result absent, the static source test expects it
absent, and the public-runner test expects it absent. The other 15 pass. The
paired scientific and durable-journal suites pass 16 of 16. These are source
and regression controls, not device or capacity evidence.

Every ADR-0394 and ADR-0395 scientific field remains binding: populations 10
and 22; both chunk families, tile orders, repeats, and all three tiles; source-
rank-major direct controls; exact work counters; 16 semantic phases; contiguous
synchronized host boundaries; worse-endpoint ratios; fixed `5/4` plus 1 ms;
90-second population, 240-second laboratory, and 180-second projection walls;
ELF and raw CUDA-13.3 resource evidence; driver/cubin maxima; 255-register,
4,096-byte backing, 131,072-thread, and 2 GB reserve gates; and null exact spill
traffic. Population 25 remains integer geometry/work/projection only.

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
ADR-0370 seals the numeric-array and logical-work result. ADR-0385 froze the
legal bridge question; ADR-0386 source-sealed only its host answer; ADR-0387
froze the consumer-capacity question; ADR-0388 source-sealed only that CuPy-
free answer; ADR-0389 froze the additive CUDA-consumer question; ADR-0390
rejected its source seal; ADR-0391 froze the first paired-tile boundary;
ADR-0392 corrected its pre-source arithmetic completeness; ADR-0393 retained
the first implementation as a wall rejection; ADR-0394 freezes the work-
preflight question; ADR-0395 corrects only its resource instrument before
result; ADR-0396 source-seals v1; ADR-0397 closes its sole invocation at worker
bootstrap; ADR-0398 freezes the additive lifecycle recovery; and ADR-0399
source-seals only that recovery. No earlier owner is revived.

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
ADR-0399 imports neither that owner nor its target. The phrases exclusive
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

## First-invocation rule

Only the clean commit containing ADR-0399 and the exact hashes above may supply
the source commit in the v2 header. Invoke only:

```powershell
$env:PYTHONPATH = "src;."
& .\.venv\Scripts\python.exe -B -m pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner
```

Do not call a private child mode, pass a config or output argument, edit an
environment mode, invoke v1, repair a file, replay after any terminal, or run a
25-card fixture. Whatever first terminal occurs is retained.

## Kill criteria

Kill or reject the owner if any source/config/v1 hash differs; Git is dirty;
the v1 artifact or v2/reserved path state differs; the literal child, challenge,
framing, import-absence, or event-order gate fails; handshake and campaign do
not share the one transport; campaign starts before the journaled handshake;
any ADR-0394/ADR-0395 science changes; population 25 is opened numerically; or
the result is compared with the 15-second action wall or used as a quality,
truncation, blueprint, or strength prior.

## Claims boundary

ADR-0399 proves source readiness and real device-free worker birth only. It
supplies no campaign child, compiler resource row, calibration value, phase
time, capacity projection, complete 25-card numerical result, resolver
iteration, solve, action, 15-second result, decision quality, truncation,
blueprint, or poker strength. The next command is eligible exactly once; it is
not pre-judged to pass.
