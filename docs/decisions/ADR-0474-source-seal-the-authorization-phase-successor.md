# ADR-0474: Source-seal the authorization-phase successor

- Status: accepted CPU-only authorization-phase successor source seal; the fresh v7 launcher, runner, independent reader, exact rejected-v6-authorization recovery layer, durable attempt and one-use launch lifecycle, repository-derived two-state authorization tag, complete successor-bound dependency proof, and source-only controls pass 20/20 with zero skips; the real checkout executes the preauthorization branch and isolated controls execute both preauthorization and live authorization; the 35-test calibration-base regression passes; four final adversarial findings were corrected before seal; the exact retained v5 attempt and rejected v6 authorization remain unchanged, every v6 and v7 lifecycle path remains absent, and no public v7 owner, compiler call, CuPy import, device work, timing value, or result exists
- Date: 2026-08-27
- Follows: ADR-0473
- Recovery config: `experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v10-authorization-phase-recovery.json`
- Recovery config bytes / canonical-LF SHA-256: `6793 / 55b0526a655099a24ce20b83bc4855f6dfb37cc5b5a7a4a213665ee93565ac38`
- Launcher: `run_legal_river_quotient_compiled_global_separation_calibration_v7.py`
- Launcher bytes / canonical-LF SHA-256: `3323 / 3dcefbcbcc6c452657e7f30dfebf191251a6616237a6386df2bce6698d5a6960`
- Runner: `src/pontius/legal_river_quotient_compiled_global_separation_calibration_v7_runner.py`
- Runner bytes / canonical-LF SHA-256: `40528 / 08fcebe7f58590b4540e438fbb35b3f639a8e0bb6dc012e131a58e4a9f077b10`
- Independent reader: `src/pontius/legal_river_quotient_compiled_global_separation_calibration_v7_result.py`
- Reader bytes / canonical-LF SHA-256: `57393 / 04f8c1bb8b135925ecbfb5cb1ce5692f4c7b44f5b6dcd72910daeb1bddec9d87`
- Controls: `tests/test_legal_river_quotient_compiled_global_separation_calibration_v7.py`
- Controls bytes / canonical-LF SHA-256: `82907 / d8c00accede7344d0a4140520b3825a5f5d049479e424ce7361c4cc443ca018a`
- Focused source-only controls / skipped: `20/20` passed / `0`
- Calibration-base, v2-outcome, and v3 regression: `35/35` passed
- Synthetic preauthorization / live-authorization phase-neutral receipts: `1 / 1`
- Real-checkout preauthorization / live-authorization receipts: `1 / 0`
- Bound dependency paths / unique paths / writer-reader agreement: `96 / 96 / true`
- Rejection aliases / started-science aliases rejected: `61 / 62`
- Retained v5 attempt bytes / raw SHA-256: `606 / 104820d0c67391365d18fb76ca72c704e40e467e2993a96c618d4bf91155600d`
- Rejected v6 authorization bytes / canonical-LF SHA-256: `482 / 57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535`
- V6 public invocations / v6 result rows / v6 attempt markers / v6 launch markers: `0 / 0 / 0 / 0`
- V7 public invocations / v7 result rows / v7 attempt markers / v7 launch markers: `0 / 0 / 0 / 0`
- Compiler calls / CuPy imports / device queries / allocations / module loads / kernel launches / timing values: `0/0/0/0/0/0/0`
- Candidate / topology / arithmetic schedule selected: `null / null / null`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0474
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472
- Front-Door-Active-Next: Create exactly one separate authorization commit whose sole parent is this source seal and whose diff is limited to the frozen six-file v7 authorization surface; then rerun all 20 focused v7 controls unchanged from that exact clean commit, require the real live-authorization ancestry, raw committed-blob, dependency-domain, environment, and lifecycle branches to pass with zero skips, and invoke the exact root v7 launcher once only if every prefire gate passes
- Front-Door-Blockers: no separate one-generation v7 invocation authorization or v7 result exists and the public v7 owner remains uninvoked; v6 is permanently closed uninvoked after its authorization gate rejected, v5 is permanently closed after its retained accidental attempt, and v4 is permanently closed uninvoked; no production source-local base producer, refresh cadence, exponent admission, or width bound exists; no selected topology, population-25 result, actual-45 numerical result, global resolver-certificate integration, complete resolver iteration, known certificate count per action, or 15-second action result exists; no repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, trained blueprint, integrated bot, production action width, or poker-strength result exists

## Question

Does fresh v7 implement the ADR-0473 authorization-state contract strongly
enough at source-seal scope to create a separate one-generation authorization?

## Decision

Yes, at source-seal scope only. Do not invoke the public owner from this ADR.
The v7 launcher, runner, independent reader, and controls are accepted as the
sole prospective successor to the permanently closed v4, v5, and v6
lifecycles. The exact 606-byte v5 attempt remains a regular, non-symlink,
non-reparse file with raw SHA-256
`104820d0c67391365d18fb76ca72c704e40e467e2993a96c618d4bf91155600d`.
The rejected v6 authorization remains a regular, byte-identical 482-byte file
whose sole-child ancestry and exact six-path diff still bind to ADR-0471. Every
v6 result, attempt, and launch path and every v7 result, attempt, and launch
path remain absent by `lexists`.

V7 separates owner lifecycle from authorization phase. One repository-derived
tag admits exactly two states. `preauthorization` requires the future v11 path
absent by `lexists`, absent from the HEAD tree, and absent from the index.
`live_authorization` requires a regular non-symlink non-reparse working file,
stage-zero index and HEAD entries naming the same ordinary blob, raw working
bytes exactly equal to that blob, exact schema and path list, sole-child
ancestry, and the exact frozen six-file diff. A supplied commit must equal the
actual HEAD. Every mixed or third state rejects. The complete tag is compared
before and after probes, bindings, lifecycle wrappers, Git readers, and result
assessment.

The common fixture no longer asserts authorization absence. It snapshots only
immutable predecessor evidence, owner-lifecycle absence, and the current exact
tag. Phase-neutral controls execute once under isolated preauthorization and
once under isolated live authorization. Crossover controls reject present-in-
source, absent-in-live, nonregular, dangling, symlink, reparse, wrong-label,
wrong-commit, wrong-blob, and canonical-LF-equivalent-but-byte-different
authorization states. The real-checkout branch has no optional or skipped
path: it observed and validated preauthorization for this seal, while the same
unchanged suite must observe live authorization after the separate commit.
No test moves, deletes, rewrites, or invokes a production owner path.

Dependency production and validation now occur inside the same complete v7
binding. Writer and reader expose the same 96 unique dependency paths; the
inherited v4 domain and every missing, extra, wrong-digest, or wrong-type domain
reject. The rejected v6 authorization is predecessor evidence only. No v6
runner, reader, assessor, public authority, or binding lock is imported or
reused. The unchanged v4 process and v3 scientific mechanics remain behind
fresh v7 protocol, campaign, result, attempt, launch, header, environment, and
authorization identities.

The final adversarial pass found four source-seal defects, all corrected before
any v7 owner or lifecycle artifact existed. First, the reader normalized CRLF
before comparing authorization working bytes to the Git blob; it now requires
raw equality, and a canonical-equivalent line-ending mutation rejects. Second,
the reader accepted a caller-supplied commit without independently requiring
actual HEAD equality; writer and reader now reject that mismatch. Third, the
inherited public parent used `exists()` for lifecycle prechecks; the root
launcher and public-parent runner path now require v7 lifecycle absence by
`lexists`, while legitimate campaign-child reentry remains exempt. Fourth, the
root launcher could inherit current-generation mode state and turn the exact
public command into a probe; it now rejects mode, challenge, spool, launch-token,
and public-pycache contamination before importing the runner. Source-only
controls cover every repair without calling `main` or the launcher's `_main`.

The launcher still tests effective `-B` and safe-path state before any non-
builtin import, rejects extension shadows, establishes a fresh external
bytecode namespace, and removes the repository root from the import path. The
runner repeats exact argv, `-B`, and `-P` validation as the first statement in
its own `main`. The source probe runs unchanged in both valid authorization
states, reports the complete tag, imports only hash-bound provenance source,
and starts no calibration science. No compiler, CuPy, device, timing, topology,
target, or numerical work contributed to this seal.

Three implementation audits plus a final independent adversarial audit found
no remaining source-seal blocker after the four corrections. The final focused
suite passes 20/20 with zero skips, and the calibration-base regression passes
35/35. These are scoped checks, not certification. Real live authorization has
not yet existed under v7; the unchanged complete suite must execute that branch
from the exact clean authorization commit. A latent implementation, driver,
compiler, or device defect can still make the one-shot run reject, and such a
failure remains retained evidence rather than retry authority.

Authorization remains external to this seal. The future authorization must use
`experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v11-authorization-phase-corrected-invocation-authorization.json`
and schema `pontius-adr0475-one-commit-v7-authorization-v1`. Its commit must be
the sole child of this source-seal commit and change exactly `ARCHITECTURE.md`,
`RISK_REGISTER.md`, `ROADMAP.md`, `STATUS.md`, the exact ADR-0475 file, and the
exact v11 config. It may not change any sealed implementation, test, recovery
config, retained marker, or lifecycle byte. Only a clean 20/20 live-phase pass
can make the exact root launcher eligible for one invocation.

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
ADR-0473 rejects that gate and closes v6 uninvoked, and ADR-0474 source-seals
only fresh v7.

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

### Source-seal boundary

Only the fresh v7 lifecycle, exact authorization-phase tag, rejected-v6
recovery layer, public-entry guards, complete source bindings, independent
reader, temporary lifecycle transitions, and CPU-only controls are sealed. The
source probe's provenance import starts no science. Compiler and device work
remain unopened. A later public v7 owner consumes the identity at attempt
creation even if authorization, launch, compiler, device, or scientific gates
reject afterward.

### Kill criteria

Kill before invocation if the retained v5 marker or rejected v6 authorization
differs by one byte; any closed predecessor or v7 unopened lifecycle path
exists even as a dangling link; the source seal and authorization are not exact
parent and child; the authorization diff is not exactly the frozen six paths;
the authorization working bytes, index blob, and HEAD blob are not identical;
any sealed dependency differs from its source-seal Git blob; the unchanged
20-test suite does not pass from clean HEAD; the real live-authorization branch
does not execute; a repository bytecode or extension shadow is present; any
legacy or current public lifecycle environment variable survives; or the owner
would run from a checkout that is not the exact authorization commit.

### Claims boundary

ADR-0474 proves only the scoped source, reader, lifecycle, authorization-phase,
and adversarial controls described above. It supplies no compiled calibration,
numerical, resource, speed, topology, population-25, target-45, resolver,
action-clock, decision-quality, truncation, blueprint, or strength result. The
independent audits and tests are spot-checking, not certification. A clean
negative first invocation remains a valid and permanently retained result.

## Consequences

- V4, v5, and v6 remain permanently closed under their recorded outcomes.
- V7 is source-sealed but not yet authorized or invoked.
- Exactly one separate ADR-0475 authorization generation may make v7 eligible.
- The unchanged full live-authorization suite and clean-state audit must pass before firing.
