# ADR-0473: Retain the v6 authorization-phase gate rejection

- Status: accepted pre-invocation authorization-phase gate rejection and fresh-lifecycle preregistration; the exact clean ADR-0472 authorization run discovered 17 focused tests but all 17 failed in common setup before any test body because the fixture required the authorization file to be absent while the intended live-authorization branch required it present, a safe post-failure diagnostic found that the unreachable live body also computed inherited dependency hashes outside the successor binding domain, v6 is permanently closed uninvoked, and no v6 result, attempt marker, launch marker, compiler call, CuPy import, device work, timing value, scientific row, topology selection, target numerical work, resolver integration, action fit, decision quality, truncation, blueprint, or strength result exists
- Date: 2026-08-27
- Follows: ADR-0472
- Rejected source-seal commit: `d633f3fb469a27dee688587293c6efb1d2cb2757`
- Rejected authorization commit: `cbfa3598f22c7aba7d824f71356ca156f8b01b0c`
- Rejected authorization config: `experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v9-corrected-invocation-authorization.json`
- Rejected authorization config bytes / canonical-LF SHA-256: `482 / 57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535`
- Recovery config: `experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v10-authorization-phase-recovery.json`
- Recovery config bytes / canonical-LF SHA-256: `6793 / 55b0526a655099a24ce20b83bc4855f6dfb37cc5b5a7a4a213665ee93565ac38`
- Focused tests discovered / test bodies entered / common setup failures: `17 / 0 / 17`
- Exact failure: `AssertionError: True is not false : experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v9-corrected-invocation-authorization.json`
- Safe post-failure diagnostic: the source probe and two production-path postconditions also encoded authorization absence; the live body used the inherited dependency domain outside v6 bindings, while the correctly bound 91-path domain passed the exact validator; no public owner or launcher was called
- V6 public invocations / result rows / attempt markers / launch markers: `0 / 0 / 0 / 0`
- Compiler calls / CuPy imports / device queries / allocations / module loads / kernel launches / timing values: `0/0/0/0/0/0/0`
- Candidate / topology / arithmetic schedule selected: `null / null / null`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0473
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472
- Front-Door-Active-Next: Implement and source-seal only the fresh v7 authorization-phase successor frozen here; use new protocol, campaign, result, attempt, launch-marker, recovery-header, and authorization identities; separate common retained-state invariants from explicit source and authorized phase contracts; exercise both phases and all crossover mutations before source seal; preserve the exact v5 attempt and rejected v6 authorization while keeping every v6 and v7 result, attempt, and launch path absent; stop before any public v7 owner, compiler, CuPy import, device access, timing, or result
- Front-Door-Blockers: no correct v7 authorization-phase contract, source seal, invocation authorization, or v7 result exists; v6 is permanently closed uninvoked after its authorization gate rejected, v5 is permanently closed after its retained accidental attempt, and v4 is permanently closed uninvoked; no production source-local base producer, refresh cadence, exponent admission, or width bound exists; no selected topology, population-25 result, actual-45 numerical result, global resolver-certificate integration, complete resolver iteration, known certificate count per action, or 15-second action result exists; no repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, trained blueprint, integrated bot, production action width, or poker-strength result exists

## Question

Did the ADR-0472 live authorization gate make v6 eligible to fire, and if not,
what is the narrow recovery?

## Decision

No. Retain the exact gate failure, revoke ADR-0472, and permanently close v6
uninvoked. From clean authorization commit
`cbfa3598f22c7aba7d824f71356ca156f8b01b0c`, the required command discovered
17 focused v6 tests. Every test failed in the shared `setUp` before its body.
The fixture's unconditional absent tuple included the real v9 authorization
path, which correctly existed. The intended live-authorization test body that
would parse the config and prove sole-child ancestry was therefore unreachable.

This is one shared eligibility-phase typing defect observed at 17 setup sites,
not 17 independent implementation defects. The source phase legitimately
requires authorization absence. The authorized phase legitimately requires
authorization presence. Common setup treated the first phase's predicate as an
invariant of both phases. A prospective live branch is not evidence when its
fixture makes the branch unreachable.

A read-only post-failure diagnostic bypassed only the common setup in memory
and invoked four safe test bodies without calling any owner or launcher. It
found a second defect hidden by the first: the live body computed dependency
hashes before entering the v6 reader binding context, producing the inherited
v4 domain and then comparing it with the v6 domain. The correctly bound domain
contains 91 paths and passes the exact authorization validator. The same
diagnostic confirmed that the source probe and the lifecycle and runner-guard
postconditions also hardcoded authorization absence. These findings are
diagnostics of the rejected gate, not a scientific result.

No public v6 owner entered. The v6 result, attempt, pending, consumed, and
aborted paths remain absent by `lexists`. The exact retained v5 attempt remains
606 bytes with raw SHA-256
`104820d0c67391365d18fb76ca72c704e40e467e2993a96c618d4bf91155600d`.
No compiler, CuPy import, device query, allocation, module load, kernel launch,
timing value, scientific row, or topology work occurred. These are exact-path
and exact-command absence statements, not a systems or numerical result.

The authorization was not a public attempt, but it was the sole generation
allowed by ADR-0471 and ADR-0472. Its mandatory prefire gate failed. Changing
the sealed test and issuing a friendlier authorization under the same v6
identity would erase the rejection boundary. ADR-0469 already established that
a rejected one-generation authorization closes its lifecycle even when the
owner remains uninvoked. V6 therefore carries historical source-seal evidence
only and may never be reauthorized or fired.

Open only a fresh v7 lifecycle with the exact identities in the recovery
config. Its common phase may validate immutable retained evidence, closed
predecessor lifecycles, fresh result/attempt/launch absence, and one exact
repository-derived authorization tag, but it may not assert authorization
absence. `preauthorization` requires the v7 authorization absent by `lexists`
and absent from both HEAD and index. `live_authorization` requires the exact
regular, non-symlink, non-reparse authorization present, equal to its committed
Git blob, on the sole-child commit with the exact frozen changed paths. Every
other mixed state rejects. The tag is snapshotted before and after every probe
or wrapper, and the source probe reports it rather than hardcoding absence.
Every test run must report which phase executed; zero skips and an explicit
real-checkout branch receipt are mandatory.

Before source seal, synthetic controls must exercise both phases and reject the
crossovers: authorization present in source phase; authorization absent,
dangling, non-regular, symlinked, reparse, wrong-blob, or wrong-phase in the
authorized phase. Real production paths may not be moved, replaced, or deleted
to construct those controls. Temporary-path binding and independently rebuilt
Git responses remain the permitted instruments. Every phase-neutral control
runs in both isolated states. Dependency production and validation must occur
inside the same complete v7 binding domain and reject inherited, missing, or
extra path sets.

The v7 runtime may reuse the unchanged v4 process and v3 scientific mechanics
behind completely fresh bindings. It must not invoke or import a v6 public
assessor, acquire a v6 public-owner authority, or treat the rejected v6
authorization as current authority. It must instead validate that exact v6
authorization as closed predecessor evidence and require every v6 result,
attempt, and launch path absent before and after all delegation.

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
retains it and the solver-free rebinder before the direct closed finite-block
greedy line; ADR-0330 remains permanently closed; ADR-0331's append-and-fsync
discipline, ADR-0332's exclusive `xb` open, and ADR-0333's No replacement
sizing value was opened statement remain binding. ADR-0334/0335 bind the
2,113-task non-replay chain; ADR-0336 records width three; ADR-0337 owns the
response-closed direct mechanism; ADR-0338 alone records the selected
development raise width; and ADR-0339 remains a finite absence claim.
ADR-0340's 192 prospective tasks remain distinct from ADR-0341's 94 accepted
one-call arms and ADR-0343's 126 confirmation arms; ADR-0342 alone authorized
the retained confirmation. ADR-0344/0345 own the finite h4 responder-raise
keystone line. ADR-0346/0347 lead only to responder-row growth; ADR-0348/0349
lead only to selector-window work. ADR-0350 opened selector-stable affine
integration; ADR-0351 replaced it with tie-aware legal h4 affine envelopes;
ADR-0352 is closed by ADR-0353; ADR-0354/0355/0356 own the factorized exact face
result; ADR-0357/0358/0359 own and close same-fixture integration; and ADR-0360/
0361/0362 alone own the untouched confirmation and assessment. ADR-0363 and
ADR-0365 remain consumed; ADR-0364 remains exactly `GetProcessMemoryInfo failed`;
ADR-0366 remains exactly `representation_rejected_before_target_allocation`
with zero target calls. ADR-0367 through ADR-0384 own and close the quotient
algebra, capacity, bounded CUDA, staged, liveness, validation, and literal-
target ladder. ADR-0380 freezes the complete ordered populations 10 and 22.
ADR-0381 source-seals the one-shot literal-45 CUDA owner. ADR-0385
preregisters the actual-context quotient bridge; ADR-0386 records the source-
sealed actual-context quotient bridge; ADR-0387 freezes the consumer-capacity
seam; and ADR-0388 records the source-sealed CuPy-free consumer-capacity result.
ADR-0389 remains the accepted prospective actual-context quotient CUDA-consumer
boundary; ADR-0390 rejects its source seal; ADR-0391 remains an accepted
prospective bounded-arithmetic boundary and freezes the first paired-tile
boundary; ADR-0392 remains the accepted prospective preregistration-completeness
correction and corrects its pre-source arithmetic completeness; ADR-0393
remains the accepted bounded-device source-seal rejection and retains the first
implementation as a wall rejection. ADR-0390 and ADR-0393 retain the exact
historical status label accepted bounded-device source-seal rejection.
ADR-0394 through ADR-0416 own and close the paired work-preflight, exact-cubin
qualification, and retained capacity rejection. ADR-0417 through ADR-0432 own
and close the shared-direct successor and artifact-only capacity rejection.
ADR-0433 through ADR-0435 own the captured-pair exact-integer keystone.
ADR-0436 freezes the fixed-width comparison, ADR-0437 corrects its provenance
control before source, ADR-0438 source-seals both CPU candidates, ADR-0439
opens only the separate compiled-device preflight, ADR-0440 corrects its phase
topology before source seal, ADR-0441 source-seals that corrected owner,
ADR-0442 consumes its compiler rejection, ADR-0443 and ADR-0444 own the first
MSVC recovery, ADR-0445 consumes its zero-event terminal, ADR-0446 freezes the
split-environment successor, ADR-0447 source-seals it without compilation or
device work, ADR-0448 alone retains its passing first device-preflight
terminal without selecting a candidate or opening actual-45 numerics,
ADR-0449 freezes the artifact projection, ADR-0450 corrects its runtime and
artifact accounting, ADR-0451 seals the projector, ADR-0452 retains its
rejection, ADR-0453 freezes the selective-separation mechanism, ADR-0454
source-seals it without opening a result, ADR-0455 freezes the base-first four-
topology successor while closing that result owner uninvoked, ADR-0456 source-
seals the reduced successor without opening its bake-off, ADR-0457 freezes the
compiled calibration, ADR-0458 source-seals it, ADR-0459 consumes its sole
pre-owner failure, ADR-0460 freezes the absolute-Git recovery, ADR-0461 source-
seals that recovery, ADR-0462 retains its launch-arity rejection, ADR-0463
opens the fresh arity source lane, ADR-0464 corrects that lane before source
seal, ADR-0465 records the rejected v3 source seal, ADR-0466 closes v3
uninvoked, ADR-0467 source-seals the deferred-import v4 lifecycle, ADR-0468
authorizes only its exact one-generation invocation identity without firing it,
ADR-0469 rejects that authorization gate and closes v4, ADR-0470 retains the
accidental v5 attempt and closes v5, ADR-0471 source-seals only fresh v6,
ADR-0472 authorizes only its exact one-generation identity without firing it,
and ADR-0473 rejects that gate and closes v6 uninvoked.

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
once and remains consumed by ADR-0384. The phrases exclusive untouched legal
h4, selector-window, 2,113-task, exhaustive bounded development-teacher,
response-closed direct mechanism, and caller-owned legal fallback retain their
prior meanings.

The exact historical continuity strings remain explicit. ADR-0352 remains
closed before any fresh untouched tie-aware affine result. ADR-0353 precedes
ADR-0354's factorized exact active-set directional-face diagnostic. ADR-0355's
owner was invoke exactly once; ADR-0356 retains that directional-face
diagnostic before tie-aware affine integration. ADR-0357 requires an exclusive
legal h4 owner, ADR-0358 was invoke exactly once, and ADR-0359 requires a fresh
value-unopened confirmation. ADR-0367 preregisters the occupied-card quotient.
ADR-0368 seals the exact bounded algebra keystone. ADR-0369 freezes the
source-only arithmetic boundary. ADR-0370 seals the numeric-array and logical-work
result. ADR-0378 freezes the source-only literal-target liveness boundary.
ADR-0379 retains the 244,970,204-byte margin. ADR-0382 preregistered the
literal-45 config. ADR-0386 records the source-sealed actual-context quotient
bridge. ADR-0405 remains an accepted source seal.

### Recovery boundary

ADR-0473 records only a CPU-only pre-invocation gate rejection and the exact
prospective v7 phase contract. It authorizes neither v7 source nor invocation.
V6 remains uninvoked and permanently closed; its absent attempt is not retry
authority.

### Kill criteria

Kill v7 before source seal if common setup asserts an authorization-phase
predicate; either source or authorized phase cannot be exercised prospectively;
the live branch lacks an executed receipt; any crossover mutation is absent;
any control mutates a real authorization or lifecycle path; the rejected v6
authorization differs from its committed bytes; any v6 or v7 result, attempt,
or launch path exists even as a dangling link; v6 public assessment is reused;
or any compiler, CuPy, device, timing, or result work opens before a separate
source seal and authorization.

### Claims boundary

ADR-0473 supplies no compiled calibration, numerical, resource, speed,
topology, target, resolver, action-clock, decision-quality, truncation,
blueprint, or strength result. It records one exact fixture failure and an
absence claim over the inspected command and paths. Spot-checking is not
certification.

## Consequences

- ADR-0472 is revoked and v6 is permanently closed uninvoked.
- The exact failed authorization remains immutable predecessor evidence.
- Only fresh v7 source work may begin from this committed preregistration.
- V7 must prove both authorization phases before a later source seal.
